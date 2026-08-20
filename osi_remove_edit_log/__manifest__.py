{
    "name": "OSI - Remove Log Note Edit Option",
    "summary": "Remove Log Note Edit Option",
    "version": "17.0",
    "author": "Open Source Integrators",
    "description": """Log Note Edit is able for all users so 
    restrict to edit and delete options from log and send message""",
    "depends": ["mail"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "osi_remove_edit_log/static/src/xml/message.xml",
        ],
    },
    "application": False,
    "installable": True,
}
