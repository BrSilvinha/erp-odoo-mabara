{
    'name': 'MABARA - Tema e interfaz',
    'version': '19.0.1.0.0',
    'category': 'Theme/Backend',
    'author': 'Proyecto ERP MABARA',
    'summary': 'Menu horizontal unico, colores corporativos y ficha de producto del maestro de materiales',
    'depends': ['web', 'mabara_service_order', 'sale_management', 'account', 'l10n_pe'],
    'data': [
        'views/product_views.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'mabara_theme/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_backend': [
            'mabara_theme/static/src/scss/mabara.scss',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'license': 'LGPL-3',
}
