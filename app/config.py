"""Configuration objects"""


class ConfigBase(object):
    title = 'Product Attribute Identification'
    keywords = 'multiple-choice, image, text, research'
    description = (
        'In this task you will identify product attributes using images and '
        'text. There are 33 products in total. The expected time to complete '
        'this HIT is less than 5 minutes.'
    )
    assignment_duration =  60 * 60 * 24 # 24 hours
    n_questions = 9


class ConfigDev(ConfigBase):
    endpoint_url = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
    submit_to_url = 'https://workersandbox.mturk.com/mturk/externalSubmit'
    max_assignments = 3
    auto_approval_delay = 60 * 60 * 24 * 30 # 1 month
    reward = '0.45'
    qualification_requirements = [
        {
            'QualificationTypeId': '2ARFPLSP75KLA8M8DH1HTEQVJT3SY6', # Masters
            'Comparator': 'Exists',
            'RequiredToPreview': False
        },
        {
            'QualificationTypeId': '00000000000000000071', # Locale
            'Comparator': 'EqualTo',
            'LocaleValue': [{
                'Country': 'US'
            }],
            'RequiredToPreview': False
        }
    ]
    lifetime = 60 * 10 # 10 Minutes


class ConfigProd(ConfigBase):
    endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'
    submit_to_url = 'https://www.mturk.com/mturk/externalSubmit'
    max_assignments = 3
    auto_approval_delay = 60 * 60 * 24 * 30 # 1 month
    lifetime = 60 * 60 * 24 * 30 # 1 month
    reward = '1.82'
    qualification_requirements = [
        {
            'QualificationTypeId': '2F1QJWKUDD8XADTFD2Q0G6UTO95ALH', # Masters
            'Comparator': 'Exists',
            'RequiredToPreview': True
        }
    ]

