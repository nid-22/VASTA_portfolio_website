TINYMCE_CONFIG = {
    "theme": "silver",
    "height": 600,

    # UI
    "menubar": "file edit view insert format tools table help",
    "branding": False,

    # Plugins
    "plugins": (
        "advlist autolink lists link image editimage charmap preview anchor "
        "searchreplace visualblocks code fullscreen "
        "insertdatetime media table wordcount help"
    ),

    # Toolbar
    "toolbar": (
        "undo redo | styleselect | fontselect fontsizeselect | "
        "bold italic underline strikethrough | forecolor backcolor | "
        "alignleft aligncenter alignright alignjustify | "
        "bullist numlist outdent indent | "
        "image media table | blockquote | removeformat | code | help"
    ),

    # Font options
    "font_family_formats": (
        "Raleway=Raleway,sans-serif;"
        "Inconsolata=Inconsolata,monospace;"
        "Georgia=georgia,serif;"
        "Times New Roman=times new roman,times,serif;"
        "Arial=arial,helvetica,sans-serif;"
    ),

    "font_size_formats": "12px 14px 16px 18px 20px 24px 28px 32px 36px",

    # Image settings
    "image_caption": True,          # ✅ Enables <figure><figcaption>
    "image_advtab": True,            # ✅ Image size, alignment, class
    "image_title": True,

    # Enable uploads from local device
    "automatic_uploads": True,
    "images_upload_url": "/tinymce/upload/",  # you must implement this view
    "file_picker_types": "image",

    # Optional but recommended
    "paste_data_images": True,       # paste images directly
    "relative_urls": False,
    "remove_script_host": False,
    "convert_urls": True,

    # Content styling (important)
    "content_style": (
        "body { font-family: Raleway, sans-serif; line-height: 1.7; }"
        "figure { margin: 2rem 0; }"
        "figcaption { font-size: 0.85rem; color: #666; text-align: center; }"
        "blockquote { font-style: italic; border-left: 3px solid #ccc; padding-left: 1rem; color: #555; }"
    ),
}
