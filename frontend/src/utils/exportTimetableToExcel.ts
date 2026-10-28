type ZipSourceFile = { path: string; content: string };

const utf8 = new TextEncoder();

function xmlEscape(value: unknown): string {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function joinBytes(parts: Uint8Array[]): Uint8Array {
  const totalLength = parts.reduce((sum, part) => sum + part.length, 0);
  const output = new Uint8Array(totalLength);
  let offset = 0;
  for (const part of parts) {
    output.set(part, offset);
    offset += part.length;
  }
  return output;
}

function crc32(bytes: Uint8Array): number {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc & 1) !== 0 ? (crc >>> 1) ^ 0xedb88320 : crc >>> 1;
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function set16(view: DataView, offset: number, value: number): void {
  view.setUint16(offset, value, true);
}

function set32(view: DataView, offset: number, value: number): void {
  view.setUint32(offset, value >>> 0, true);
}

/** Produces a valid ZIP archive with uncompressed entries. */
function makeZip(files: ZipSourceFile[]): Uint8Array {
  const localParts: Uint8Array[] = [];
  const centralParts: Uint8Array[] = [];
  let localOffset = 0;

  for (const file of files) {
    const nameBytes = utf8.encode(file.path);
    const dataBytes = utf8.encode(file.content);
    const checksum = crc32(dataBytes);
    const localHeader = new Uint8Array(30 + nameBytes.length);
    const localView = new DataView(localHeader.buffer);
    set32(localView, 0, 0x04034b50);
    set16(localView, 4, 20);
    set16(localView, 6, 0);
    set16(localView, 8, 0);
    set16(localView, 10, 0);
    set16(localView, 12, 0x0021);
    set32(localView, 14, checksum);
    set32(localView, 18, dataBytes.length);
    set32(localView, 22, dataBytes.length);
    set16(localView, 26, nameBytes.length);
    set16(localView, 28, 0);
    localHeader.set(nameBytes, 30);
    localParts.push(localHeader, dataBytes);

    const centralHeader = new Uint8Array(46 + nameBytes.length);
    const centralView = new DataView(centralHeader.buffer);
    set32(centralView, 0, 0x02014b50);
    set16(centralView, 4, 20);
    set16(centralView, 6, 20);
    set16(centralView, 8, 0);
    set16(centralView, 10, 0);
    set16(centralView, 12, 0);
    set16(centralView, 14, 0x0021);
    set32(centralView, 16, checksum);
    set32(centralView, 20, dataBytes.length);
    set32(centralView, 24, dataBytes.length);
    set16(centralView, 28, nameBytes.length);
    set16(centralView, 30, 0);
    set16(centralView, 32, 0);
    set16(centralView, 34, 0);
    set16(centralView, 36, 0);
    set32(centralView, 38, 0);
    set32(centralView, 42, localOffset);
    centralHeader.set(nameBytes, 46);
    centralParts.push(centralHeader);
    localOffset += localHeader.length + dataBytes.length;
  }

  const centralDirectory = joinBytes(centralParts);
  const endRecord = new Uint8Array(22);
  const endView = new DataView(endRecord.buffer);
  set32(endView, 0, 0x06054b50);
  set16(endView, 4, 0);
  set16(endView, 6, 0);
  set16(endView, 8, files.length);
  set16(endView, 10, files.length);
  set32(endView, 12, centralDirectory.length);
  set32(endView, 16, localOffset);
  set16(endView, 20, 0);
  return joinBytes([...localParts, centralDirectory, endRecord]);
}

function columnName(index: number): string {
  let result = "";
  let number = index;
  while (number > 0) {
    const remainder = (number - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    number = Math.floor((number - 1) / 26);
  }
  return result;
}

function cellXml(value: unknown, cellRef: string, style: number): string {
  return '<c r="' + cellRef + '" s="' + style + '" t="inlineStr"><is><t xml:space="preserve">' +
    xmlEscape(value) + "</t></is></c>";
}

function createWorksheet(headers: string[], rows: string[][]): string {
  const allRows = [headers, ...rows];
  const lastColumn = columnName(headers.length);
  const lastRow = allRows.length;
  const columnWidths = [14, 19, 25, 13, 25, 25];
  const columnsXml = headers.map((_, index) => {
    const width = columnWidths[index] ?? 22;
    return '<col min="' + (index + 1) + '" max="' + (index + 1) +
      '" width="' + width + '" customWidth="1"/>';
  }).join("");

  const rowsXml = allRows.map((row, rowIndex) => {
    const rowNumber = rowIndex + 1;
    const isHeader = rowIndex === 0;
    const rowStyle = isHeader ? 1 : (rowIndex % 2 === 0 ? 3 : 2);
    const height = isHeader ? 28 : 22;
    const cells = headers.map((_, columnIndex) => {
      const value = row[columnIndex] ?? "";
      const style = isHeader ? 1 : (rowIndex % 2 === 0 ? 3 : 2);
      return cellXml(value, columnName(columnIndex + 1) + rowNumber, style);
    }).join("");
    return '<row r="' + rowNumber + '" ht="' + height + '" customHeight="1" s="' +
      rowStyle + '">' + cells + "</row>";
  }).join("");

  return [
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
    '  <sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>',
    '  <dimension ref="A1:' + lastColumn + lastRow + '"/>',
    '  <sheetViews><sheetView showGridLines="0" workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>',
    '  <sheetFormatPr defaultRowHeight="20"/>',
    '  <cols>' + columnsXml + '</cols>',
    '  <sheetData>' + rowsXml + '</sheetData>',
    '  <autoFilter ref="A1:' + lastColumn + lastRow + '"/>',
    '  <pageMargins left="0.25" right="0.25" top="0.5" bottom="0.5" header="0.2" footer="0.2"/>',
    '  <pageSetup paperSize="9" orientation="landscape" fitToWidth="1" fitToHeight="0"/>',
    '</worksheet>',
  ].join("\n");
}

const CONTENT_TYPES = [
  '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
  '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
  '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
  '  <Default Extension="xml" ContentType="application/xml"/>',
  '  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
  '  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>',
  '  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
  '  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
  '  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
  '</Types>',
].join("\n");

const ROOT_RELS = [
  '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
  '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>',
  '  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>',
  '  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>',
  '</Relationships>',
].join("\n");

const WORKBOOK = [
  '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
  '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
  '  <bookViews><workbookView xWindow="0" yWindow="0" windowWidth="24000" windowHeight="12000"/></bookViews>',
  '  <sheets><sheet name="Grade completa" sheetId="1" r:id="rId1"/></sheets>',
  '  <calcPr calcId="191029"/>',
  '</workbook>',
].join("\n");

const WORKBOOK_RELS = [
  '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
  '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>',
  '  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>',
  '</Relationships>',
].join("\n");

const STYLES = [
  '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
  '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
  '  <fonts count="2"><font><sz val="11"/><name val="Aptos"/><family val="2"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="10"/><name val="Aptos"/><family val="2"/></font></fonts>',
  '  <fills count="4"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFB20000"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFF9EAEA"/><bgColor indexed="64"/></patternFill></fill></fills>',
  '  <borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border><border><left style="thin"><color rgb="FFD9DEE5"/></left><right style="thin"><color rgb="FFD9DEE5"/></right><top style="thin"><color rgb="FFD9DEE5"/></top><bottom style="thin"><color rgb="FFD9DEE5"/></bottom><diagonal/></border></borders>',
  '  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>',
  '  <cellXfs count="4"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"><alignment vertical="center"/></xf><xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf><xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf><xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf></cellXfs>',
  '  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>',
  '</styleSheet>',
].join("\n");

const CORE_PROPERTIES = [
  '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
  '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">',
  '  <dc:creator>Anatinus</dc:creator><dc:title>Grade horária completa</dc:title><dc:subject>Exportação de horários escolares</dc:subject>',
  '</cp:coreProperties>',
].join("\n");

const APP_PROPERTIES = [
  '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
  '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">',
  '  <Application>Anatinus</Application>',
  '</Properties>',
].join("\n");

/** Downloads a genuine .xlsx workbook with widths, filters, frozen header and alternating rows. */
export function exportTimetableToExcel(
  headers: string[],
  rows: string[][],
  fileName = "anatinus-grade.xlsx",
): void {
  if (headers.length === 0) {
    throw new Error("A exportação precisa de cabeçalhos.");
  }

  const archive = makeZip([
    { path: "[Content_Types].xml", content: CONTENT_TYPES },
    { path: "_rels/.rels", content: ROOT_RELS },
    { path: "xl/workbook.xml", content: WORKBOOK },
    { path: "xl/_rels/workbook.xml.rels", content: WORKBOOK_RELS },
    { path: "xl/worksheets/sheet1.xml", content: createWorksheet(headers, rows) },
    { path: "xl/styles.xml", content: STYLES },
    { path: "docProps/core.xml", content: CORE_PROPERTIES },
    { path: "docProps/app.xml", content: APP_PROPERTIES },
  ]);

  const blob = new Blob(
    [archive.buffer as ArrayBuffer],
    { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
  );
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
