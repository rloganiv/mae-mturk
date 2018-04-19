"""Command-line script for creating questionairres."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json
from itertools import cycle

from app.vocab import ValueSet


FLAGS = None


def load_value_set(fname):
    """Loads a serialized ValueSet."""
    with open(fname, 'r') as f:
        value_set = ValueSet.load(f)
    return value_set


def load_known_data(fname):
    """Loads known data."""
    with open(FLAGS.known_answers, 'r') as f:
        known_answer_data = json.load(f)
    known_uris = {entry['diffbotUri'] for entry in known_answer_data}
    known_iterator = cycle(known_answers) # Loop when generating
    return known_iterator, known_uris


def generate_products(fnames):
    """Generates products one at a time."""
    for fname in fnames:
        with open(fname, 'r') as f:
            products = json.load(f)
        for product in products:
            yield product


def has_category(product, category):
    """Whether or not product has specified category."""
    if (category is None) and ('category' not in product):
        return True
    elif product['category'] == category:
        return True
    else:
        return False


class QuestionnaireBuilder(object):
    def __init__(self,
                 known_iterator,
                 known_uris,
                 value_set,
                 max_size,
                 questionnaire_size,
                 prevent_duplicates=False):
        """Used to build questionnaire files.

        Args:
            known_iterator: An iterator which produces known answers.
            known_uris: A set of known answer uris. Used to prevent mistakenly adding
                attribute queries for products whose attributes are known as
                questions to the questionairre.
            value_set: A ValueSet object, defining the space of possible values
                for each product attribute.
            max_size: Maximum number of questions enqueue.
            questionnaire_size: Number of questions to add per form.
            prevent_duplicates: Whether or not to allow multiple instances of
                an attribute-value pair to appear in the questionairre.
        """
        self._known_iterator = known_iterator
        self._known_uris = known_uris
        self._value_set = value_set
        self._max_size = max_size
        self._questionnaire_size = questionnaire_size
        self._prevent_duplicates = prevent_duplicates
        if self._prevent_duplicates:
            self._seen_pairs = set()

        self._questions = []
        self._images = set()

    class QuestionQueueFull(Exception):
        """Custom exception raised when question queue is full."""
        pass

    def _check_queue_size(self):
        """Checks if the question queue is full. If it is then a
        QuetionQueueFull exception is raised.
        """
        if len(self._questions) > self._max_size:
            raise QuestionnaireBuilder.QuestionQueueFull()

    def add(self, product):
        """Enqueues questions derived from a product.

        Args:
            product: A dictionary containing product data.
        """
        # If product attributes are known then skip.
        if product['diffbotUri'] in self._known_uris:
            return None

        # Otherwise, enqueue a question for each attribute-value pair.
        for attr, value in product['specs']:

            # If enabled, handle duplicate pairs.
            if self._prevent_duplicates:
                if (attr, value) in self._seen_pairs:
                    continue
                else:
                    self._seen_pairs.add((attr, value))

            # Construct the question.
            options = self._generate_options(attr, value)
            question = {
                'diffbotUri': product['diffbotUri'],
                'known': False,
                'title': product['title'],
                'images': product['images'],
                'description': product['description'],
                'attribute': attr,
                'correct_value': value,
                'options': options
            }
            self._questions.append(question)

            # Add product images to the image set.
            self._images.update(product['images'])

            # Lastly, check if queue is full.
            self._check_queue_size()

    def generate_questionnaires(self):
        # Shuffle the list of questions in place.
        random.shuffle(self._questions)
        l = len(self._questions)
        q = self._questionnaire_size

        # Retrieve the questions.
        for i in range(l // q):

            # Select the block of questions.
            questionnaire['questions'] = self._questions[i*q:(i+1)*q]

            # Get the next known question, answer pair.
            known = next(self._known_iterator)

            # Only add the known question to the questionnaire.
            known['question']['known'] = True # Ensure question is 'known'.
            questionnaire.append(known['question'])

            # Shuffle questionnaire before outputting. This makes it so that
            # the known question appears randomly in each questionnaire instead
            # of in the same place.
            random.shuffle(questionnaire)

            yield questionnaire

    @property
    def image_list(self):
        return list(self._images)

    @image_list.setter
    def image_list(self, x):
        raise AttributeError('Cannot assign QuestionnaireBuilder.image_list')


def main(_):
    # Load data
    value_set = load_value_set(FLAGS.value_set)
    known_iterator, known_uris = load_known_data(FLAGS.known)

    # Initialize questionnaire builder
    builder = QuestionnaireBuilder(known_iterator,
                                   known_uris,
                                   value_set,
                                   FLAGS.max_size,
                                   FLAGS.questionnaire_size,
                                   FLAGS.prevent_duplicates)

    # Add questions to questionnaire.
    print('Enqueuing questions...')
    for product in generate_products(FLAGS.inputs):
        if has_category(product, FLAGS.category):
            try:
                questionnaire_builder.add(product)
            except QuestionQueueFull:
                break

    # Output questionnaires.
    print('Writing questionnaires...')
    for i, questionnaire in builder.generate_questionnaires():
        fname = '%s_%i.json' % (FLAGS.output_prefix, i)
        with open(fname, 'w') as f:
            json.dump(questionnaire)

    # Output image list.
    print('Writing image list...')
    fname = '%s_image_list.txt' % FLAGS.output_prefix
    with open(fname, 'w') as f:
        for image in builder.image_list:
            f.write('%s\n' % image)

    print('Done.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--known', type=str, default=None, required=True,
                        help='JSON file containing known answers.')
    parser.add_argument('--value_set', type=str, default=None, required=True,
                        help='Text file containing value set data.')
    parser.add_argument('--max_size', type=int, default=None, required=True,
                        help='Maximum number of questions.')
    parser.add_argument('--questionnaire_size', type=int, default=None,
                        required=True,
                        help='Number of questions in each questionnaire.')
    parser.add_argument('--category_filter', type=str, default=None,
                        help='Questions are only generated for a specific '
                             'category of products. Default is to select '
                             'products with no category.')
    parser.add_argument('--prevent_duplicates', action='store_true',
                        help='Whether to prevent duplicate attribute-value '
                             'pairs from occuring in the questionnaire.')
    parser.add_argument('output_prefix', type=str,
                        help='Prefix for output files.')
    parser.add_argument('inputs', nargs='+', type=str,
                        help='JSON files from the MAE dataset.')
    FLAGS, _ = parser.parse_known_args()

    main(_)

