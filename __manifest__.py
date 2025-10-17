{
    'name': 'ADDICAPP Ahorros',
    'version': '1.0.0',
    'summary': 'Administrador de contribuciones y ahorros en ADDICAPP',
    'description': 'Diseñado para gestionar los ahorros y contribuciones de una asociación. Permite a los '
                   'administradores definir tipos de ahorros, registrar los ahorros y contribuciones de los afiliados, '
                   'visualizar las aportaciones de cada uno de los afiliados y generar reportes oficiales de los ahorros.',
    'author': 'Telematica',
    'category': 'Accounting',
    'depends': ['base', 'accountant', 'mail'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/contributions_manager_saving_types_view.xml',
        'views/contributions_manager_contribution_types_view.xml',
        'views/contributions_manager_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tel_capp_csm/static/img/icon.png',
        ],
    },
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'auto_install': False,
}