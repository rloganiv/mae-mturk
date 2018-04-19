"""Deploy HITs on Mechanical Turk."""

import argparse
import boto3
import sys

from config import ConfigDev, ConfigProd


FLAGS = None


def construct_hit_review_policy(config):
    """Constructs a HIT review policy.

    The policy checks for agreement on each question.
    """
    checked_fields = ['selectedValue%i', 'usedImage%i', 'usedText%i',
                      'usedDescription%i']
    hit_review_policy = {
        'PolicyName': 'SimplePlurality/2011-09-01',
        'Parameters': [
            {'Key': 'QuestionIds',
             'Values': [field % i for field in checked_fields
                        for i in range(min(config.n_questions, 25))]},
            {'Key': 'QuestionAgreementThreshold',
             'Values': ['100']},
            {'Key': 'ApproveIfWorkerAgreementScoreIsAtLeast',
             'Values': ['85']} # Must agree with 7/8 answers
        ]
    }
    return hit_review_policy


def construct_assignment_review_policy(answer_key):
    """Constructs an assignment review policy.

    The policy checks that the submission is 100% accurate on a known example.
    If it is not, then the assignment is automatically rejected and the HIT is
    extended by one assingment.

    Args:
        answer_key: An AnswerKey object.
    """
    assignment_review_policy = {
        'PolicyName': 'ScoreMyKnownAnswers/2011-09-01',
        'Parameters': [
            {'Key': 'RejectIfKnownAnswerScoreIsLessThan',
             'Values': ['100']},
            {'Key': 'ExtendIfKnownAnswerScoreIsLessThan',
             'Values': ['100']},
            {'Key': 'RejectReason',
             'Values': ['To ensure high-quality responses we include a question '
                        'in this survey where we already know the attribute '
                        'value as well as which pieces of information are used '
                        'to find it. Your work was rejected since you either '
                        'failed to identify the correct value or did not '
                        'identify all of the pieces of information used to find '
                        'it. We apologize for the inconvenience.']}
            {'Key': 'AnswerKey',
             'MapEntries': answer_key.map_entries}
    }


def main(_):
    # Validate CLI parameters
    if not FLAGS.prod and not FLAGS.dev:
        print('Either --prod or --dev must be specified.')
        sys.exit(1)

    # Load configuration
    if FLAGS.prod:
        config = ConfigProd()
    elif FLAGS.dev:
        config = ConfigDev()

    # Create client and load external question
    client = boto3.client('mturk', endpoint_url=config.endpoint_url)

    # Create HITType
    response = client.create_hit_type(
        AutoApprovalDelayInSeconds=config.auto_approval_delay,
        AssignmentDurationInSeconds=config.assignment_duration,
        Reward=config.reward,
        Title=config.title,
        Keywords=config.keywords,
        Description=config.description,
        QualificationRequirements=config.qualification_requirements)
    hit_type_id = response['HITTypeId']
    print(f'HITTypeID: {hit_type_id}')

    # Create review poliicy
    hit_review_policy = construct_hit_review_policy(config)

    # Get external question template
    with open('external_question.xml', 'r') as f:
        external_question = f.read()

    # Deploy questions
    for question_file in FLAGS.question_files:
        question = external_question.format(question_file=question_file)
        assignment_review_policy = construct_assignment_review_policy(answer_key)
        response = client.create_hit_with_hit_type(
            HITTypeId=hit_type_id,
            MaxAssignments=config.max_assignments,
            LifetimeInSeconds=config.lifetime,
            HITReviewPolicy=hit_review_policy,
            AssignmentReviewPolicy=assignment_review_policy,
            Question=question)
        hit_id = response['HIT']['HITId']
        print(f'{hit_id}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prod', action='store_true')
    parser.add_argument('--dev', action='store_true')
    FLAGS, _ = parser.parse_known_args()

    main(_)

