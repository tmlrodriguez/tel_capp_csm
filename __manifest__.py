{
    'name': 'Ahorros',
    'version': '1.0.0',
    'summary': 'Administrador de contribuciones y ahorros en ADDICAPP',
    'description': 'Diseñado para gestionar los ahorros y contribuciones de una asociación. Permite a los '
                   'administradores definir tipos de ahorros, registrar los ahorros y contribuciones de los afiliados, '
                   'visualizar las aportaciones de cada uno de los afiliados y generar reportes oficiales de los ahorros.',
    'author': 'Telematica',
    'category': 'Accounting',
    'depends': ['base', 'accountant', 'mail'],
    'data': [
        # Data
        'data/ir_sequence_data.xml',
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        # Views
        'views/res_partner_view.xml',
        'views/account_journal_view.xml',
        'views/account_payment_view.xml',
        'views/account_payment_view_inherit_withdrawal.xml',
        'views/contributions_manager_dashboard_view.xml',
        'views/contributions_partner_contribution_popup_form.xml',
        'views/contributions_manager_contribution_types_view.xml',
        'views/contributions_manager_contributions_view.xml',
        'views/contributions_manager_withdrawals_view.xml',
        'views/contributions_manager_menu.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'tel_capp_csm/static/src/css/global.css',
            'tel_capp_csm/static/img/icon.png',
        ],
    },
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'auto_install': False,
}