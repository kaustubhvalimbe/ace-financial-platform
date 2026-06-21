/**
 * Ace Financial Services — CAS Issue Reporter (Tier 1)
 * ─────────────────────────────────────────────────────
 * This script receives "Report This Issue" submissions from the
 * Analyse My Portfolio screen and logs them to a Google Sheet.
 *
 * It does NOT auto-fix anything — it just captures the raw CAS text
 * and context so Kaustubh + Claude can review it and patch the parser,
 * the same way every CAS format has been handled so far.
 *
 * SETUP INSTRUCTIONS:
 * 1. Go to sheets.google.com → create a new blank spreadsheet
 *    (name it something like "Ace CAS Issue Reports")
 * 2. In that sheet: Extensions → Apps Script
 * 3. Delete any starter code in the editor, paste this entire file
 * 4. Click the Save icon (or Ctrl+S)
 * 5. Click "Deploy" (top right) → "New deployment"
 * 6. Click the gear icon next to "Select type" → choose "Web app"
 * 7. Fill in:
 *      Description: CAS Issue Reporter
 *      Execute as: Me
 *      Who has access: Anyone
 * 8. Click "Deploy" — it may ask you to authorize access, approve it
 * 9. Copy the "Web app URL" it gives you (ends in /exec)
 * 10. Paste that URL into investment-case.html, replacing the
 *     placeholder value of the ANL_REPORT_WEBHOOK_URL constant
 *     (near the top of the Analyse My Portfolio script section)
 *
 * Whenever someone reports an issue, a new row appears automatically
 * in this spreadsheet — no further setup needed after this.
 */

function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

  // Add header row once, if the sheet is empty
  if (sheet.getLastRow() === 0) {
    sheet.appendRow([
      'Timestamp', 'Contact (Name/WhatsApp)', 'Detected CAS Type',
      'Status', 'Status Message', 'Funds Found', 'Flagged Count',
      'Raw CAS Text', 'Browser Info'
    ]);
    sheet.setFrozenRows(1);
  }

  var p = e.parameter || {};

  sheet.appendRow([
    new Date(),
    p.contact || '(not provided)',
    p.casType || '(unrecognized)',
    p.status || '',
    p.statusMsg || '',
    p.fundsFound || '0',
    p.flaggedCount || '0',
    p.rawText || '',
    p.userAgent || ''
  ]);

  return ContentService
    .createTextOutput(JSON.stringify({ result: 'success' }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  return ContentService.createTextOutput(
    'Ace Financial Services — CAS Issue Reporter webhook. This endpoint accepts POST requests only.'
  );
}
