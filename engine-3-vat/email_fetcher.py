"""IMAP email scanner — downloads invoice PDF attachments."""

import imaplib
import email
import os
import tempfile
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class EmailFetcher:
    def __init__(self, host: str, port: int, user: str, password: str,
                 ssl: bool = True):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.ssl = ssl
        self.conn: Optional[imaplib.IMAP4_SSL] = None

    def connect(self):
        try:
            if self.ssl:
                self.conn = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                self.conn = imaplib.IMAP4(self.host, self.port)
            self.conn.login(self.user, self.password)
            logger.info("IMAP connected to %s as %s", self.host, self.user)
        except imaplib.IMAP4.error as e:
            raise ConnectionError(f"IMAP login failed: {e}") from e

    def disconnect(self):
        if self.conn:
            try:
                self.conn.logout()
            except Exception:
                pass
            self.conn = None

    def fetch_pdf_attachments(
        self,
        folder: str = "INBOX",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> list[dict]:
        """
        Fetch PDF attachments from inbox within date range.

        Returns list of dicts: {filename, filepath, subject, sender, date}
        """
        if not self.conn:
            raise RuntimeError("Not connected. Call connect() first.")

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="vat_engine_")

        os.makedirs(output_dir, exist_ok=True)

        try:
            self.conn.select(folder, readonly=True)
        except imaplib.IMAP4.error as e:
            logger.warning("Could not select folder %s: %s", folder, e)
            return []

        # Build IMAP search criteria
        criteria = []
        if date_from:
            dt = datetime.strptime(date_from, "%Y-%m-%d")
            criteria.append(f'SINCE "{dt.strftime("%d-%b-%Y")}"')
        if date_to:
            dt = datetime.strptime(date_to, "%Y-%m-%d")
            criteria.append(f'BEFORE "{dt.strftime("%d-%b-%Y")}"')

        search_str = " ".join(criteria) if criteria else "ALL"

        try:
            status, message_ids = self.conn.search(None, search_str)
        except imaplib.IMAP4.error as e:
            logger.error("IMAP search failed: %s", e)
            return []

        if status != "OK" or not message_ids[0]:
            return []

        results = []
        ids = message_ids[0].split()
        logger.info("Found %d emails to scan", len(ids))

        for msg_id in ids:
            try:
                status, msg_data = self.conn.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = self._decode_header(msg.get("Subject", ""))
                sender = self._decode_header(msg.get("From", ""))
                date_str = msg.get("Date", "")

                # Walk MIME parts looking for PDFs
                for part in msg.walk():
                    content_type = part.get_content_type()
                    disposition = str(part.get("Content-Disposition", ""))

                    is_pdf = (
                        content_type == "application/pdf"
                        or "filename" in disposition.lower()
                        and part.get_filename("").lower().endswith(".pdf")
                    )

                    if not is_pdf:
                        continue

                    filename = part.get_filename("")
                    if not filename:
                        filename = f"attachment_{msg_id.decode()}.pdf"

                    # Sanitize filename
                    safe_name = "".join(
                        c for c in filename if c.isalnum() or c in "._- "
                    ).strip()
                    if not safe_name:
                        safe_name = f"invoice_{msg_id.decode()}.pdf"

                    filepath = os.path.join(output_dir, safe_name)

                    # Avoid overwriting with a counter suffix
                    base, ext = os.path.splitext(filepath)
                    counter = 1
                    while os.path.exists(filepath):
                        filepath = f"{base}_{counter}{ext}"
                        counter += 1

                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))

                    results.append({
                        "filename": safe_name,
                        "filepath": filepath,
                        "subject": subject,
                        "sender": sender,
                        "date": date_str,
                    })
                    logger.info("Saved attachment: %s", safe_name)

            except Exception as e:
                logger.warning("Error processing email %s: %s", msg_id, e)
                continue

        return results

    @staticmethod
    def _decode_header(value: str) -> str:
        if not value:
            return ""
        parts = email.header.decode_header(value)
        decoded = []
        for part, charset in parts:
            if isinstance(part, bytes):
                decoded.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                decoded.append(str(part))
        return " ".join(decoded)


def fetch_invoices_from_config(config: dict, output_dir: str = None) -> list[dict]:
    """
    High-level helper: fetch PDFs from all configured email accounts.
    Returns merged list of attachment dicts.
    """
    scan_cfg = config.get("scan", {})
    date_from = scan_cfg.get("date_from")
    date_to = scan_cfg.get("date_to")

    all_attachments = []
    for account in config.get("email", {}).get("accounts", []):
        fetcher = EmailFetcher(
            host=account["host"],
            port=account.get("port", 993),
            user=account["user"],
            password=account["password"],
            ssl=account.get("ssl", True),
        )
        try:
            fetcher.connect()
            folders = account.get("folders", ["INBOX"])
            for folder in folders:
                attachments = fetcher.fetch_pdf_attachments(
                    folder=folder,
                    date_from=date_from,
                    date_to=date_to,
                    output_dir=output_dir,
                )
                all_attachments.extend(attachments)
        except Exception as e:
            logger.error("Failed to fetch from %s: %s", account["host"], e)
        finally:
            fetcher.disconnect()

    return all_attachments
