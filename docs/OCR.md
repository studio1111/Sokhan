# Local OCR for scanned PDFs

Sokhan's OCR adapter is opt-in and runs on the machine executing the command. It uses PyMuPDF's Tesseract integration; installing the Python extra does **not** install the Tesseract executable or language data.

## Install

Install the Tesseract executable and the language packs you need with your operating system's package manager. On Debian or Ubuntu:

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-fas
python -m pip install -e ".[pdf,ocr]"
```

On macOS, install Tesseract with Homebrew (`brew install tesseract`) and then install Sokhan's OCR extra. On Windows, install a trusted Tesseract distribution, ensure its executable is on `PATH`, install the required `tessdata` language files, then install `.[pdf,ocr]`.

Check the installed language codes with `tesseract --list-langs`. Common codes are `eng` for English and `fas` for Persian. Combined language recognition can use a code such as `eng+fas` when both language packs are installed.

## Use

Extract text from a scanned PDF:

```bash
sokhan extract-pdf scan.pdf --ocr --ocr-language eng --ocr-dpi 300
```

Translate a scanned PDF to a Persian RTL PDF:

```bash
sokhan pdf-to-fa scan.pdf translated.fa.pdf \
  --font /path/to/NotoNaskhArabic-Regular.ttf \
  --ocr --ocr-language eng --ocr-dpi 300
```

OCR can be enabled for extraction and translation with `--ocr`. It is disabled by default; ordinary text PDFs continue to use their native text layer without invoking Tesseract.

## Limits and failure behavior

- DPI is restricted to 72–600; the default is 300.
- The default maximum is 200 pages; the configurable hard ceiling is 2,000 pages.
- The requested language identifier is validated before invoking OCR.
- Encrypted PDFs are rejected.
- Missing PyMuPDF, the Tesseract executable, or language data produces an actionable local error. There is no cloud fallback.
- Sokhan does not download OCR engines, models, or language packs.
- OCR quality depends on scan resolution, skew, contrast, layout, and installed language data. Tables, columns, handwriting, and complex page geometry are not reconstructed.
- OCR output is plain text; the original PDF layout is not preserved by the text extraction workflow.

No document text is logged or uploaded by Sokhan. Treat OCR text as untrusted input when sending it to a separately configured translation model.
