Manage Mechanical Turk HITs for MAE Dataset Validation
===

This repository contains a collection of scripts and utilities for deploying
and managing labelling tasks for the MAE dataset on Mechanical Turk.


Creating Questionnaires
---

The key task for crowd workers is complete questionnaires, which are tracked as
seperate JSON files. Each questionnaire is comprised of a list of `question`
objects. Questions pertain to a single attribute of a single product in the MAE
dataset. They have the following fields:

- `question.title`: The title of the product.
- `question.images`: The images depicting the product.
- `question.description`: The description of the product.
- `question.attribute`: The attribute query.
- `question.correct_value`: The answer to the attribute query according to the
  MAE dataset. Note that one may not actually be able to determine this value
  from the provided context.
- `question.options`: The potential values visible to crowd workers.
- `question.known`: Whether or not the answer to the question is known. A known
  question is included with each questionnaire to be used to check the quality
  of crowd worker submissions.

Questionairres can by using the `create_questionnaires` command-line utility:
```{bash}
python -m app.utils.create_questionnaires [see help for options]
```
In order to use this utility, you will need access to the MAE dataset JSON
files. You will also need a collection of known answer files.

Deploying HITs
---

In order to deploy HITs, you will need to upload the questionnaires and product
images to an AWS server (TODO: create a shell script to facilitate this
process).

You can then use the `deploy` command-line utility:
```{bash}
python -m app.deploy \h
    --dev [or --prod] \
    --known PATH TO KNOWN ANSWERS FILE \
    [QUESTIONNAIRE FILES TO DEPLOY]
```
Specifying the `--dev` flag will deploy the HITs to the Mechanical Turk Sandbox
environment, you should do this to ensure that there are no problems with the
HIT before deploying to production.
To deploy to the actual Mechanical Turk website, use the `--prod` flag instead.


Checking HITs
---

To reduce the burden of checking worker submissions:
- Any HITs where workers faiyl to correctly answer the known question are
  automatically rejected.
- Any HITs where workers agree on the answers to all unknown questions are
  automatically accepted. (TODO: Make sure to exclude the known question when
  deploying).
Any HIT which is not automatically accepted/rejected must be manually reviewed.
To help with this review process we have designed a simple flask app for
reviewing. This can be used by running:
```{bash}
flask run app.py
```
And then entering the URL printed out in your browser.


Collecting Results
---
To collect results run:
```{bash}
python -m app.collect_results [see help for options]
```
