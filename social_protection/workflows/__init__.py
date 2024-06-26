"""
Overview

The Python workflows detailed here are designed to facilitate the validation and processing
of beneficiary upload data within a development environment.
These workflows implement a series of steps to ensure that uploaded data meets specific criteria,
both in terms of content and structure, before proceeding with database operations.

Important Note: These workflows are intended for use in a development (dev) environment.
They are executed in a single-threaded manner, which may not be efficient for processing larger batches of data.
Their primary purpose is to illustrate the concept of beneficiary upload workflows and similar processes.

Development Use and Efficiency Considerations

    Single-Threaded Execution: Given that these workflows operate in a single-threaded context,
    they may exhibit limitations in processing speed and efficiency when handling large datasets.

    Development Environment Application: It is recommended to utilize these workflows within
    a dev environment to explore and understand the underlying concepts of beneficiary data upload and processing.
    They serve as a foundational guide for developing more robust, production-ready solutions.

"""
from social_protection.workflows.base_beneficiary_upload import process_import_beneficiaries_workflow
from social_protection.workflows.base_beneficiary_update import process_update_beneficiaries_workflow

from social_protection.workflows.beneficiary_update_valid import process_update_valid_beneficiaries_workflow
from social_protection.workflows.beneficiary_upload_valid import process_import_valid_beneficiaries_workflow
