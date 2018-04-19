import boto3
import csv
from collections import namedtuple
from xml.etree import ElementTree
from deploy import ConfigProd


Answer = namedtuple('Answer', ['uri', 'attribute', 'correct_value',
                               'selected_value', 'used_image',
                               'used_title', 'used_desc'])


def parse_answers(answer_xml):
    pairs = dict()
    answers = []

    # Parse XML
    namespaces = {'xmlns': 'http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionFormAnswers.xsd'}
    root = ElementTree.fromstring(answer_xml)
    children = root.findall('xmlns:Answer', namespaces=namespaces)
    for child in children:
        key = child.find('xmlns:QuestionIdentifier', namespaces=namespaces).text
        value = child.find('xmlns:FreeText', namespaces=namespaces).text
        pairs[key] = value

    # Convert results to namedtuples
    for i in range(33): #  TODO: Make a parameter
        try:
            uri = pairs['diffbotUri%i' % i]
            attribute = pairs['attribute%i' % i]
            correct_value = pairs['correctValue%i' % i]
            selected_value = pairs['selectedValue%i' % i]
            used_image = pairs['usedImage%i' % i]
            used_title = pairs['usedTitle%i' % i]
            used_desc = pairs['usedDescription%i' % i]
            answer = Answer(uri, attribute, correct_value, selected_value,
                            used_image, used_title, used_desc)
            answers.append(answer)
        except:
            pass

    return answers


def main(_):
    config = ConfigProd()
    client = boto3.client('mturk', endpoint_url=config.endpoint_url)
    next_token = None

    answers = []
    n_tot = 0

    while True:
        # Obtain a collection of HITs
        if next_token:
            response = client.list_hits(MaxResults=100, NextToken=next_token)
        else:
            response = client.list_hits(MaxResults=100)

        # If list is empty then break
        if response['NumResults'] == 0:
            break

        # Collect answers for each HIT
        for hit in response['HITs']:
            hit_id = hit['HITId']
            assignments = client.list_assignments_for_hit(HITId=hit_id)
            assignments = assignments['Assignments']
            for assignment in assignments:
                n_tot += 1
                answer_xml = assignment['Answer']
                parsed = parse_answers(answer_xml)
                answers.extend(parsed)

        next_token = response['NextToken']

    # Write a CSV
    with open('answers.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(('uri', 'attribute', 'correct_value',
                          'selected_value', 'used_image',
                          'used_title', 'used_desc'))
        writer.writerows([(x.uri, x.attribute, x.correct_value,
                           x.selected_value, x.used_image,
                           x.used_title, x.used_desc) for x in answers])
    print(n_tot)


if __name__ == '__main__':
    main(None)

