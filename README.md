# سخن | Sokhan

**سخن** ابزار متن‌باز و محلی‌محور برای تبدیل محتوای انگلیسی به فارسی طبیعی است. هدف پروژه فقط ترجمه کلمه‌به‌کلمه نیست؛ بلکه حفظ معنا، نیت گوینده، لحن و زمان‌بندی است.

> وضعیت فعلی: ابزارهای متن و زیرنویس، استخراج و ترجمه PDF متنی با خروجی فارسی راست‌چین، استخراج صوت، ASR اختیاری و آداپتر TTS محلی پیاده‌سازی شده‌اند. مدل TTS باید جداگانه نصب و ارزیابی شود؛ کلون صدا، تشخیص گوینده و تحلیل احساس هنوز قابلیت آماده محصول نیستند.

## قابلیت‌ها

| قابلیت | وضعیت |
|---|---|
| یکسان‌سازی نویسه‌ها و فاصله‌گذاری فارسی | پیاده‌سازی شده |
| اعتبارسنجی، خواندن و نوشتن SRT/VTT | پیاده‌سازی شده |
| ترجمه SRT/VTT با حفظ زمان cueها | پیاده‌سازی شده |
| افزایش زمان نمایش SRT بر پایه نرخ خواندن و بدون هم‌پوشانی | heuristic پیاده‌سازی شده؛ نه word alignment |
| اتصال ترجمه به مدل محلی سازگار با OpenAI | پیاده‌سازی شده؛ بدون fallback ابری |
| استخراج متن PDF متنی | پیاده‌سازی شده |
| OCR محلی PDF اسکن‌شده | اختیاری؛ نیازمند PyMuPDF، Tesseract و بسته زبان |
| ترجمه PDF متنی و ساخت PDF فارسی RTL | پیاده‌سازی شده؛ نیازمند فونت TTF مناسب |
| استخراج صوت با FFmpeg | پیاده‌سازی شده |
| ASR انگلیسی با faster-whisper | اختیاری؛ زمان‌بندی segment و word حفظ می‌شود |
| اتصال به TTS محلی OpenAI-compatible | adapter و CLI پیاده‌سازی شده؛ نیازمند موتور سازگار |
| word alignment، diarization و emotion/prosody | در دست توسعه |
| cross-lingual voice cloning و دوبله نهایی | در دست توسعه؛ نیازمند رضایت و ارزیابی مجوز |
| رابط دسکتاپ/وب و سامانه ایجنت پژوهش/بازبین | در دست توسعه |

## نصب

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,pdf]"
pytest
ruff check .
~~~

برای ASR:
~~~bash
python -m pip install -e ".[audio]"
~~~

## PDF فارسی

یک فایل PDF متنی یا اسکن‌شده را با مدل ترجمه محلی به فارسی تبدیل کنید. یک فونت TrueType با پوشش حروف فارسی باید از قبل روی دستگاه موجود باشد؛ فونت پروژه یا مدل فونت را دانلود نمی‌کند. برای PDF اسکن‌شده، OCR باید صریحاً فعال شود و Tesseract و بسته زبان مربوطه از قبل نصب باشند.

~~~bash
sokhan extract-pdf source.pdf
sokhan extract-pdf scan.pdf --ocr --ocr-language eng --ocr-dpi 300
sokhan pdf-to-fa scan.pdf translated.fa.pdf --font /path/to/NotoNaskhArabic-Regular.ttf --ocr --ocr-language eng
~~~

ترجمه در قطعه‌های محدود انجام می‌شود. خروجی موجود بازنویسی نمی‌شود. OCR به‌صورت پیش‌فرض خاموش است، حداکثر ۲۰۰ صفحه و DPI بین ۷۲ تا ۶۰۰ را می‌پذیرد و هیچ موتور یا بسته زبانی را خودکار دانلود نمی‌کند. جزئیات نصب در `docs/OCR.md` آمده است.

## زیرنویس و صوت

~~~bash
sokhan translate-srt captions.en.srt captions.fa.srt
sokhan srt-fit captions.fa.srt readable.fa.srt --media-duration-ms 125000 --max-cps 17
sokhan translate-vtt captions.en.vtt captions.fa.vtt
sokhan extract-audio input.mp4 audio.wav
python -m pip install -e ".[audio]"
sokhan audio-to-srt audio.wav output.fa.srt --asr-model small.en --device cpu
~~~

مدل ASR در نخستین اجرا ممکن است دانلود و در cache محلی نگهداری شود. فایل ویدئو بازسازی یا دوبله نمی‌شود.

## TTS محلی

~~~bash
export SOKHAN_TTS_BASE_URL=http://127.0.0.1:1234
export SOKHAN_TTS_MODEL=your-local-tts-model
export SOKHAN_TTS_VOICE=default
sokhan text-to-speech persian.txt output.wav
~~~

آداپتر از endpoint سازگار با OpenAI در مسیر `/v1/audio/speech` استفاده می‌کند. endpoint فقط localhost است و redirect یا fallback ابری مجاز نیست. نام مدل و voice باید با موتور محلی شما سازگار باشد. هیچ مدل TTS یا وزن صوتی همراه بسته نصب نمی‌شود.

## مدل ترجمه محلی

~~~bash
export SOKHAN_LLM_BASE_URL=http://127.0.0.1:1234
export SOKHAN_LLM_MODEL=your-local-model
sokhan translate input.txt --register conversational
~~~

حالت پیش‌فرض فقط میزبان‌های محلی را می‌پذیرد. endpoint خارجی تنها با تنظیم صریح `SOKHAN_ALLOW_EXTERNAL_PROVIDER=true` و HTTPS فعال می‌شود.

## CI و نگه‌داری

- تست Python و Ruff روی Python 3.11 تا 3.13.
- تحلیل امنیتی CodeQL و به‌روزرسانی هفتگی وابستگی‌ها با Dependabot.
- تست مستقل سیاست retention با Node.js.
- گردش‌کار روزانه فقط ۳۰ اجرای کامل‌شدهٔ آخر هر workflow را نگه می‌دارد؛ اجراهای درحال‌اجرا حذف نمی‌شوند.
- گردش‌کار کیفیت هفتگی گزارش deterministic تولید می‌کند.
- وزن مدل‌ها و فایل صوتی کاربران در CI ذخیره نمی‌شوند.
- ادغام خودکار و نوشتن مستقیم روی main مجاز نیست.

## مدل‌ها و حریم خصوصی

مدل‌های TTS و مجوز وزن‌ها در `docs/MODEL_REGISTRY.md` ثبت شده‌اند. هیچ مدل نامزد به‌عنوان موتور production تأیید نشده است. کلون‌کردن صدای افراد فقط با رضایت روشن و مجوز معتبر مجاز خواهد بود. جزئیات در `docs/PRIVACY.md` آمده است.

## مجوز

کد پروژه تحت MIT منتشر می‌شود. مجوز مدل‌ها، وزن‌ها و دیتاست‌های شخص ثالث مستقل است.
