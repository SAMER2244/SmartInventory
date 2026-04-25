"""
SmartInventory i18n — Centralized Translation Dictionary
==================================================
All user-facing strings in Turkish (tr), English (en), and Arabic (ar).
Organised by UI section for maintainability.

Adding a new string:
    1. Add a key here with all 3 translations.
    2. Use  t('your_key')  in app.py or any Streamlit-facing module.
"""

TRANSLATIONS: dict[str, dict[str, str]] = {

    # ── Page Config & Title ──────────────────────────────────────────────
    "page_title": {
        "tr": "Envanter Yönetim Sistemi",
        "en": "Inventory Management System",
        "ar": "نظام إدارة المخزون",
    },
    "main_heading": {
        "tr": "Envanter Yönetim Sistemi",
        "en": "Inventory Management System",
        "ar": "نظام إدارة المخزون",
    },

    # ── Tab Labels ────────────────────────────────────────────────────────
    "tab_stock": {
        "tr": "📦 Stok Yönetimi",
        "en": "📦 Stock Management",
        "ar": "📦 إدارة المخزون",
    },
    "tab_shipment": {
        "tr": "🚚 Sevkiyat Analizi",
        "en": "🚚 Shipment Analysis",
        "ar": "🚚 تحليل الشحنات",
    },
    "tab_settings": {
        "tr": "⚙️ Ayarlar",
        "en": "⚙️ Settings",
        "ar": "⚙️ الإعدادات",
    },

    # ── Stock Tab ─────────────────────────────────────────────────────────
    "stock_subheader": {
        "tr": "📦 Stok Yönetimi & Veritabanı Düzenleyici",
        "en": "📦 Stock Management & Database Editor",
        "ar": "📦 إدارة المخزون ومحرر قاعدة البيانات",
    },
    "search_placeholder": {
        "tr": "🔍 Parça Ara (Manufacturer Part, Comment, Designator...):",
        "en": "🔍 Search Parts (Manufacturer Part, Comment, Designator...):",
        "ar": "🔍 بحث القطع (رقم القطعة، التعليق، المحدد...):",
    },
    "critical_threshold": {
        "tr": "🔴 Kritik Stok Eşiği:",
        "en": "🔴 Critical Stock Threshold:",
        "ar": "🔴 حد المخزون الحرج:",
    },
    "col_manufacturer_part": {
        "tr": "Manufacturer Part",
        "en": "Manufacturer Part",
        "ar": "رقم القطعة",
    },
    "col_quantity": {
        "tr": "Adet",
        "en": "Quantity",
        "ar": "الكمية",
    },
    "col_last_updated": {
        "tr": "Son Güncelleme",
        "en": "Last Updated",
        "ar": "آخر تحديث",
    },
    "btn_save_db": {
        "tr": "💾 Değişiklikleri Veritabanına Kaydet",
        "en": "💾 Save Changes to Database",
        "ar": "💾 حفظ التغييرات في قاعدة البيانات",
    },
    "success_db_updated": {
        "tr": "Veritabanı başarıyla güncellendi!",
        "en": "Database updated successfully!",
        "ar": "!تم تحديث قاعدة البيانات بنجاح",
    },
    "error_save": {
        "tr": "Kayıt hatası: {e}",
        "en": "Save error: {e}",
        "ar": "خطأ في الحفظ: {e}",
    },
    "caption_total_parts": {
        "tr": "Toplam {count} parça gösteriliyor.",
        "en": "Showing {count} parts total.",
        "ar": "عرض {count} قطعة إجمالاً.",
    },
    "info_db_empty": {
        "tr": "Veritabanı boş. Ayarlar sekmesinden migration başlatın.",
        "en": "Database is empty. Start migration from the Settings tab.",
        "ar": "قاعدة البيانات فارغة. ابدأ الترحيل من تبويب الإعدادات.",
    },
    "error_table_display": {
        "tr": "Tablo görüntüleme hatası: {e}",
        "en": "Table display error: {e}",
        "ar": "خطأ في عرض الجدول: {e}",
    },
    "caption_column_types": {
        "tr": "  Sütun '{col}': tipler={types}, dtype={dtype}",
        "en": "  Column '{col}': types={types}, dtype={dtype}",
        "ar": "  العمود '{col}': أنواع={types}, dtype={dtype}",
    },

    # ── Shipment Tab ──────────────────────────────────────────────────────
    "shipment_subheader": {
        "tr": "🚚 Sevkiyat & Eksiklik Analizi",
        "en": "🚚 Shipment & Shortage Analysis",
        "ar": "🚚 تحليل الشحنات والنقص",
    },
    "radio_operation_type": {
        "tr": "İşlem Tipi:",
        "en": "Operation Type:",
        "ar": "نوع العملية:",
    },
    "radio_shortage_analysis": {
        "tr": "📊 Eksik Parça Analizi (BOM vs SQL)",
        "en": "📊 Shortage Analysis (BOM vs SQL)",
        "ar": "📊 تحليل النقص (BOM مقابل SQL)",
    },
    "radio_restock": {
        "tr": "📥 Stok Güncelleme (Yeni Sevkiyat)",
        "en": "📥 Stock Update (New Shipment)",
        "ar": "📥 تحديث المخزون (شحنة جديدة)",
    },
    "upload_center": {
        "tr": "### 📤 Dosya Yükleme Merkezi",
        "en": "### 📤 File Upload Center",
        "ar": "### 📤 مركز رفع الملفات",
    },
    "upload_bom": {
        "tr": "Analiz Edilecek / Stoktan Düşülecek Liste (.xlsx)",
        "en": "BOM / Deduction List (.xlsx)",
        "ar": "قائمة التحليل / الخصم من المخزون (.xlsx)",
    },
    "upload_bom_help": {
        "tr": "Analiz etmek istediğiniz BOM veya sevkiyat listesini buraya yükleyin. "
              "İşlem sonunda veritabanı miktarını buradan düşebilirsiniz.",
        "en": "Upload the BOM or shipment list you want to analyse. "
              "You can deduct from the database at the end of the process.",
        "ar": "قم بتحميل قائمة BOM أو الشحنة التي تريد تحليلها. "
              "يمكنك الخصم من قاعدة البيانات في نهاية العملية.",
    },
    "upload_external_stock": {
        "tr": "Harici/Geçici Stok Dosyası (Veritabanı Yerine Kullanılır)",
        "en": "External / Temporary Stock File (Used Instead of Database)",
        "ar": "ملف مخزون خارجي / مؤقت (يُستخدم بدلاً من قاعدة البيانات)",
    },
    "upload_external_stock_help": {
        "tr": "Opsiyoneldir. Buraya dosya yüklerseniz, sistem ana veritabanını "
              "kullanmak yerine bu dosyayı baz alır.",
        "en": "Optional. If you upload a file here, the system will use this file "
              "instead of the main database.",
        "ar": "اختياري. إذا قمت بتحميل ملف هنا، سيستخدم النظام هذا الملف "
              "بدلاً من قاعدة البيانات الرئيسية.",
    },
    "upload_shipment": {
        "tr": "Gelen Sevkiyat Dosyası (.xlsx)",
        "en": "Incoming Shipment File (.xlsx)",
        "ar": "ملف الشحنة الواردة (.xlsx)",
    },
    "btn_start_analysis": {
        "tr": "Analizi Başlat",
        "en": "Start Analysis",
        "ar": "بدء التحليل",
    },
    "btn_update_stock": {
        "tr": "Stokları Güncelle",
        "en": "Update Stock",
        "ar": "تحديث المخزون",
    },
    "spinner_analysing": {
        "tr": "Analiz ediliyor...",
        "en": "Analysing...",
        "ar": "...جاري التحليل",
    },
    "spinner_updating": {
        "tr": "Güncelleniyor...",
        "en": "Updating...",
        "ar": "...جاري التحديث",
    },
    "error_generic": {
        "tr": "Hata: {e}",
        "en": "Error: {e}",
        "ar": "خطأ: {e}",
    },
    "success_restock": {
        "tr": "Başarılı! {updated} güncellendi, {new} yeni eklendi.",
        "en": "Success! {updated} updated, {new} new parts added.",
        "ar": "!نجاح! تم تحديث {updated}، وإضافة {new} قطع جديدة.",
    },
    "label_analysis_result": {
        "tr": "Analiz Sonucu:",
        "en": "Analysis Result:",
        "ar": "نتيجة التحليل:",
    },
    "btn_consume": {
        "tr": "🔴 Stoktan Düş (Tüketim Onayla)",
        "en": "🔴 Deduct from Stock (Confirm Consumption)",
        "ar": "🔴 خصم من المخزون (تأكيد الاستهلاك)",
    },
    "btn_clear": {
        "tr": "Temizle",
        "en": "Clear",
        "ar": "مسح",
    },
    "success_consumed": {
        "tr": "Stoklar başarıyla düşüldü!",
        "en": "Stock successfully deducted!",
        "ar": "!تم خصم المخزون بنجاح",
    },
    "error_consumption": {
        "tr": "Tüketim hatası: {e}",
        "en": "Consumption error: {e}",
        "ar": "خطأ في الاستهلاك: {e}",
    },

    # ── Settings Tab ──────────────────────────────────────────────────────
    "settings_subheader": {
        "tr": "⚙️ Sistem Ayarları",
        "en": "⚙️ System Settings",
        "ar": "⚙️ إعدادات النظام",
    },
    "label_language": {
        "tr": "🌐 Dil / Language / اللغة:",
        "en": "🌐 Language / Dil / اللغة:",
        "ar": "🌐 اللغة / Dil / Language:",
    },
    "btn_save_keys": {
        "tr": "🔑 Anahtarları Kaydet",
        "en": "🔑 Save API Keys",
        "ar": "🔑 حفظ مفاتيح API",
    },
    "success_keys_saved": {
        "tr": "Kaydedildi!",
        "en": "Saved!",
        "ar": "!تم الحفظ",
    },
    "data_transfer_subheader": {
        "tr": "🔄 Veri Transferi",
        "en": "🔄 Data Transfer",
        "ar": "🔄 نقل البيانات",
    },
    "btn_migration": {
        "tr": "🚀 Excel'den SQL'e İlk Migration (data/1.xlsx)",
        "en": "🚀 Initial Migration: Excel → SQL (data/1.xlsx)",
        "ar": "🚀 الترحيل الأولي: Excel ← SQL (data/1.xlsx)",
    },
    "info_detected_structure": {
        "tr": "Tespit edilen yapı: {struct}",
        "en": "Detected structure: {struct}",
        "ar": "الهيكل المكتشف: {struct}",
    },
    "success_migration": {
        "tr": "Migration başarıyla tamamlandı!",
        "en": "Migration completed successfully!",
        "ar": "!تم الترحيل بنجاح",
    },
    "error_file_not_found": {
        "tr": "data/1.xlsx bulunamadı!",
        "en": "data/1.xlsx not found!",
        "ar": "!data/1.xlsx لم يتم العثور على",
    },
    "db_status_subheader": {
        "tr": "🔬 Veritabanı Durum",
        "en": "🔬 Database Status",
        "ar": "🔬 حالة قاعدة البيانات",
    },
    "label_columns": {
        "tr": "**Sütunlar ({count}):** {cols}",
        "en": "**Columns ({count}):** {cols}",
        "ar": "**الأعمدة ({count}):** {cols}",
    },
    "label_record_count": {
        "tr": "**Kayıt Sayısı:** {count}",
        "en": "**Record Count:** {count}",
        "ar": "**عدد السجلات:** {count}",
    },
    "label_data_types": {
        "tr": "**Veri Tipleri:**",
        "en": "**Data Types:**",
        "ar": "**أنواع البيانات:**",
    },
    "label_first_row_types": {
        "tr": "**İlk Satır Python Tipleri:**",
        "en": "**First Row Python Types:**",
        "ar": "**أنواع بايثون للصف الأول:**",
    },
    "warning_db_read_error": {
        "tr": "DB okuma hatası: {e}",
        "en": "DB read error: {e}",
        "ar": "خطأ في قراءة قاعدة البيانات: {e}",
    },

    # ── Shutdown Button ───────────────────────────────────────────────────
    "btn_shutdown_help": {
        "tr": "Sistemi Kapat",
        "en": "Shutdown System",
        "ar": "إيقاف النظام",
    },

    # ── Column Not Found Error ────────────────────────────────────────────
    "error_column_not_found": {
        "tr": "Sütun bulunamadı: {col}. Mevcut sütunlar: {cols}",
        "en": "Column not found: {col}. Available columns: {cols}",
        "ar": "العمود غير موجود: {col}. الأعمدة المتاحة: {cols}",
    },

    # ── Processor Error ───────────────────────────────────────────────────
    "error_excel_structure": {
        "tr": "Excel yapı tespiti hatası: {e}",
        "en": "Excel structure detection error: {e}",
        "ar": "خطأ في كشف بنية Excel: {e}",
    },
}
