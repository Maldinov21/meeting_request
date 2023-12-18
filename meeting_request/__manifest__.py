# -*- coding: utf-8 -*-
{
    'name': "Meeting Request",
    'description': 'Meeting Request Module',
    'author': "Maldinov",
    'website': "-",
    'category': 'Meeting',
    'version': '1',
    'depends': ['base','website', 'calendar', 'contacts'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/mail_templates.xml',
        'views/menu.xml',
        'views/meeting_request.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
