"""
Email MCP Server

Ein MCP-Server für Email-Operationen.
Unterstützt SMTP (Senden) und IMAP (Lesen).
"""

from fastmcp import FastMCP
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header
from typing import Optional
import os
import json
from datetime import datetime

mcp = FastMCP("email-server")


def get_smtp_config() -> dict:
    """Holt SMTP-Konfiguration aus Umgebungsvariablen."""
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "use_tls": os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
    }


def get_imap_config() -> dict:
    """Holt IMAP-Konfiguration aus Umgebungsvariablen."""
    return {
        "host": os.environ.get("IMAP_HOST", "imap.gmail.com"),
        "port": int(os.environ.get("IMAP_PORT", "993")),
        "user": os.environ.get("IMAP_USER", ""),
        "password": os.environ.get("IMAP_PASSWORD", ""),
        "use_ssl": os.environ.get("IMAP_USE_SSL", "true").lower() == "true"
    }


def decode_email_header(header_value: str) -> str:
    """Dekodiert Email-Header."""
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            result.append(part)
    return "".join(result)


# ============================================================================
# SMTP (SENDEN)
# ============================================================================

@mcp.tool
def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = None,
    bcc: str = None,
    html: bool = False
) -> dict:
    """
    Sendet eine Email.
    
    Args:
        to: Empfänger-Adresse(n), komma-getrennt
        subject: Betreff
        body: Email-Text
        cc: CC-Adressen (optional)
        bcc: BCC-Adressen (optional)
        html: Ob der Body HTML ist (default: False)
    
    Returns:
        Status der Sendung
    """
    config = get_smtp_config()
    
    if not config["user"] or not config["password"]:
        return {"error": "SMTP nicht konfiguriert. Setze SMTP_USER und SMTP_PASSWORD"}
    
    try:
        # Message erstellen
        msg = MIMEMultipart("alternative")
        msg["From"] = config["user"]
        msg["To"] = to
        msg["Subject"] = subject
        
        if cc:
            msg["Cc"] = cc
        
        # Body hinzufügen
        if html:
            msg.attach(MIMEText(body, "html", "utf-8"))
        else:
            msg.attach(MIMEText(body, "plain", "utf-8"))
        
        # Alle Empfänger sammeln
        recipients = [addr.strip() for addr in to.split(",")]
        if cc:
            recipients.extend([addr.strip() for addr in cc.split(",")])
        if bcc:
            recipients.extend([addr.strip() for addr in bcc.split(",")])
        
        # Verbinden und senden
        with smtplib.SMTP(config["host"], config["port"]) as server:
            if config["use_tls"]:
                server.starttls()
            server.login(config["user"], config["password"])
            server.sendmail(config["user"], recipients, msg.as_string())
        
        return {
            "success": True,
            "message": f"Email an {to} gesendet",
            "subject": subject,
            "recipients": len(recipients)
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def check_smtp_config() -> dict:
    """
    Prüft die SMTP-Konfiguration.
    
    Returns:
        Konfigurationsstatus
    """
    config = get_smtp_config()
    
    # Passwort maskieren
    masked_password = "****" if config["password"] else "(nicht gesetzt)"
    
    return {
        "host": config["host"],
        "port": config["port"],
        "user": config["user"] or "(nicht gesetzt)",
        "password": masked_password,
        "use_tls": config["use_tls"],
        "configured": bool(config["user"] and config["password"])
    }


@mcp.tool
def test_smtp_connection() -> dict:
    """
    Testet die SMTP-Verbindung.
    
    Returns:
        Verbindungsstatus
    """
    config = get_smtp_config()
    
    if not config["user"] or not config["password"]:
        return {"success": False, "error": "SMTP nicht konfiguriert"}
    
    try:
        with smtplib.SMTP(config["host"], config["port"]) as server:
            if config["use_tls"]:
                server.starttls()
            server.login(config["user"], config["password"])
        
        return {
            "success": True,
            "message": f"SMTP-Verbindung zu {config['host']} erfolgreich"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# IMAP (LESEN)
# ============================================================================

@mcp.tool
def list_mailboxes() -> dict:
    """
    Listet alle verfügbaren Mailboxen/Ordner.
    
    Returns:
        Liste der Mailboxen
    """
    config = get_imap_config()
    
    if not config["user"] or not config["password"]:
        return {"error": "IMAP nicht konfiguriert. Setze IMAP_USER und IMAP_PASSWORD"}
    
    try:
        if config["use_ssl"]:
            imap = imaplib.IMAP4_SSL(config["host"], config["port"])
        else:
            imap = imaplib.IMAP4(config["host"], config["port"])
        
        imap.login(config["user"], config["password"])
        
        status, mailboxes = imap.list()
        
        folders = []
        if status == "OK":
            for mailbox in mailboxes:
                if mailbox:
                    # Parse Mailbox-Name
                    decoded = mailbox.decode() if isinstance(mailbox, bytes) else mailbox
                    # Extrahiere Namen (letzter Teil nach Leerzeichen und Quotes)
                    parts = decoded.split('" "')
                    if len(parts) >= 2:
                        name = parts[-1].strip('"')
                    else:
                        name = decoded.split()[-1].strip('"')
                    folders.append(name)
        
        imap.logout()
        
        return {
            "success": True,
            "mailboxes": folders
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_emails(
    mailbox: str = "INBOX",
    count: int = 10,
    unread_only: bool = False
) -> dict:
    """
    Holt Emails aus einer Mailbox.
    
    Args:
        mailbox: Mailbox-Name (default: INBOX)
        count: Anzahl der Emails (default: 10)
        unread_only: Nur ungelesene Emails (default: False)
    
    Returns:
        Liste der Emails
    """
    config = get_imap_config()
    
    if not config["user"] or not config["password"]:
        return {"error": "IMAP nicht konfiguriert"}
    
    try:
        if config["use_ssl"]:
            imap = imaplib.IMAP4_SSL(config["host"], config["port"])
        else:
            imap = imaplib.IMAP4(config["host"], config["port"])
        
        imap.login(config["user"], config["password"])
        imap.select(mailbox)
        
        # Suche
        search_criteria = "UNSEEN" if unread_only else "ALL"
        status, message_ids = imap.search(None, search_criteria)
        
        if status != "OK":
            imap.logout()
            return {"error": "Suche fehlgeschlagen"}
        
        ids = message_ids[0].split()
        # Neueste zuerst
        ids = ids[-count:] if len(ids) > count else ids
        ids = list(reversed(ids))
        
        emails = []
        for msg_id in ids:
            status, msg_data = imap.fetch(msg_id, "(RFC822)")
            if status == "OK" and msg_data[0]:
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Body extrahieren
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode("utf-8", errors="replace")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="replace")
                
                emails.append({
                    "id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                    "from": decode_email_header(msg.get("From", "")),
                    "to": decode_email_header(msg.get("To", "")),
                    "subject": decode_email_header(msg.get("Subject", "")),
                    "date": msg.get("Date", ""),
                    "body": body[:2000]  # Erste 2000 Zeichen
                })
        
        imap.logout()
        
        return {
            "mailbox": mailbox,
            "total_fetched": len(emails),
            "emails": emails
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def search_emails(
    query: str,
    mailbox: str = "INBOX",
    max_results: int = 20
) -> dict:
    """
    Sucht nach Emails.
    
    Args:
        query: Suchbegriff (wird in Subject gesucht)
        mailbox: Mailbox-Name
        max_results: Maximale Ergebnisse
    
    Returns:
        Gefundene Emails
    """
    config = get_imap_config()
    
    if not config["user"] or not config["password"]:
        return {"error": "IMAP nicht konfiguriert"}
    
    try:
        if config["use_ssl"]:
            imap = imaplib.IMAP4_SSL(config["host"], config["port"])
        else:
            imap = imaplib.IMAP4(config["host"], config["port"])
        
        imap.login(config["user"], config["password"])
        imap.select(mailbox)
        
        # IMAP-Suche
        status, message_ids = imap.search(None, f'SUBJECT "{query}"')
        
        if status != "OK":
            imap.logout()
            return {"error": "Suche fehlgeschlagen"}
        
        ids = message_ids[0].split()
        ids = ids[-max_results:] if len(ids) > max_results else ids
        ids = list(reversed(ids))
        
        emails = []
        for msg_id in ids:
            status, msg_data = imap.fetch(msg_id, "(BODY[HEADER.FIELDS (FROM TO SUBJECT DATE)])")
            if status == "OK" and msg_data[0]:
                header = msg_data[0][1]
                msg = email.message_from_bytes(header)
                
                emails.append({
                    "id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                    "from": decode_email_header(msg.get("From", "")),
                    "subject": decode_email_header(msg.get("Subject", "")),
                    "date": msg.get("Date", "")
                })
        
        imap.logout()
        
        return {
            "query": query,
            "mailbox": mailbox,
            "total_found": len(emails),
            "emails": emails
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def get_email_by_id(email_id: str, mailbox: str = "INBOX") -> dict:
    """
    Holt eine spezifische Email anhand ihrer ID.
    
    Args:
        email_id: Email-ID
        mailbox: Mailbox-Name
    
    Returns:
        Email-Details
    """
    config = get_imap_config()
    
    if not config["user"] or not config["password"]:
        return {"error": "IMAP nicht konfiguriert"}
    
    try:
        if config["use_ssl"]:
            imap = imaplib.IMAP4_SSL(config["host"], config["port"])
        else:
            imap = imaplib.IMAP4(config["host"], config["port"])
        
        imap.login(config["user"], config["password"])
        imap.select(mailbox)
        
        status, msg_data = imap.fetch(email_id.encode(), "(RFC822)")
        
        if status != "OK" or not msg_data[0]:
            imap.logout()
            return {"error": f"Email {email_id} nicht gefunden"}
        
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Body und Attachments extrahieren
        body_text = ""
        body_html = ""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": decode_email_header(filename),
                            "content_type": content_type,
                            "size": len(part.get_payload(decode=True) or b"")
                        })
                elif content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode("utf-8", errors="replace")
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_html = payload.decode("utf-8", errors="replace")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body_text = payload.decode("utf-8", errors="replace")
        
        imap.logout()
        
        return {
            "id": email_id,
            "from": decode_email_header(msg.get("From", "")),
            "to": decode_email_header(msg.get("To", "")),
            "cc": decode_email_header(msg.get("Cc", "")),
            "subject": decode_email_header(msg.get("Subject", "")),
            "date": msg.get("Date", ""),
            "body_text": body_text[:10000],
            "body_html": body_html[:10000] if body_html else None,
            "attachments": attachments
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool
def check_imap_config() -> dict:
    """
    Prüft die IMAP-Konfiguration.
    
    Returns:
        Konfigurationsstatus
    """
    config = get_imap_config()
    
    masked_password = "****" if config["password"] else "(nicht gesetzt)"
    
    return {
        "host": config["host"],
        "port": config["port"],
        "user": config["user"] or "(nicht gesetzt)",
        "password": masked_password,
        "use_ssl": config["use_ssl"],
        "configured": bool(config["user"] and config["password"])
    }


# ============================================================================
# RESOURCE
# ============================================================================

@mcp.resource("email://config")
def email_config() -> str:
    """Aktuelle Email-Konfiguration."""
    smtp = check_smtp_config()
    imap = check_imap_config()
    return json.dumps({
        "smtp": smtp,
        "imap": imap
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
