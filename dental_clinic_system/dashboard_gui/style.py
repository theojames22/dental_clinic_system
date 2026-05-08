class Config:
    DB_HOST = 'localhost'
    DB_NAME = 'dental_clinic_db'
    DB_USER = 'root'
    DB_PASSWORD = ''
    
    # Color scheme
    COLORS = {
        "bg": "#F0F4F8",
        "white": "#FFFFFF",
        "primary": "#2C5F8A",
        "primary_dark": "#1E405E",
        "primary_light": "#4A8BB7",
        "secondary": "#00A896",
        "secondary_dark": "#028070",
        "danger": "#DC3545",
        "warning": "#FFC107",
        "info": "#17A2B8",
        "text": "#2D3748",
        "text_light": "#718096",
        "dark": "#1A202C",
        "border": "#E2E8F0",
        "success": "#28A745",
        "hover_primary": "#3A6F9A",
        "hover_secondary": "#1AB89E",
        "hover_info": "#2EB5D0"
    }
    
    # Window settings
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 700
    MIN_WIDTH = 1500
    MIN_HEIGHT = 800

    # App settings
    APP_NAME = "LC Dental Care"

    # SMTP Configuration for Email Recovery
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_EMAIL = "theojamesnicdao26@gmail.com"
    SMTP_PASSWORD = "txvp ibzi yvpm qxrs"
    SMTP_FROM_NAME = "LC Dental Care"
    SMTP_USE_TLS = True
    SMTP_USE_SSL = False