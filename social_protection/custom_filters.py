import logging

from collections import namedtuple
from typing import List

from core.custom_filters import CustomFilterWizardInterface
from social_protection.models import BenefitPlan


logger = logging.getLogger(__name__)


class BenefitPlanCustomFilterWizard(CustomFilterWizardInterface):

    OBJECT_CLASS = BenefitPlan

    def get_type_of_object(self) -> str:
        """
            Get the type of object for which we want to define a specific way of building filters.

            Returns:
                str: The type of the object.
        """
        return self.OBJECT_CLASS.__name__

    def load_definition(self, tuple_type: type, **kwargs) -> List[namedtuple]:
        """
            Load the definition of how to create filters.

            This method retrieves the definition of how to create filters and returns it as a list of named tuples.
            Each named tuple is built with the provided `tuple_type` and has the fields `field`, `filter`, and `value`.

            Example named tuple: <Type>(field=<str>, filter=<str>, value=<str>)
            Example usage: BenefitPlan(field='income', filter='lt, gte, icontains, exact', type='')

            Args:
                tuple_type (type): The type of the named tuple.

            Returns:
                List[namedtuple]: A list of named tuples representing the definition of how to create filters.
        """
        logger.info('starting loading definition of custom filter')
        list_of_tuple_with_definitions = []
        benefit_plan_id = kwargs.get('uuid', None)
        if benefit_plan_id:
            benefit_plan = BenefitPlan.objects.filter(id=benefit_plan_id).first()
            if benefit_plan:
                self.__process_schema_and_build_tuple(benefit_plan, tuple_type, list_of_tuple_with_definitions)
            else:
                logger.info('There is no benefit plan with such id')
        else:
            logger.info('Id of benefit plan is not provided')
        logger.info('Output is prepared with definition how to build filters')
        return list_of_tuple_with_definitions

    def __process_schema_and_build_tuple(
        self,
        benefit_plan: BenefitPlan,
        tuple_type: type,
        list_of_tuple_with_definitions: List[namedtuple]
    ) -> None:
        """
            Process the schema for the obtained BenefitPlan instance and load the schema
            definition into the desired output.

            Args:
                benefit_plan (BenefitPlan): The instance of the chosen BenefitPlan where the schema is
                 presented for a specific program.
                tuple_type (type): The type of the named tuple.
                list_of_tuple_with_definitions (List[namedtuple]): A list of named tuples representing
                 the definition of how to create filters.

            Returns:
                None: This is a void method.
        """
        schema = benefit_plan.beneficiary_data_schema
        if schema:
            if 'properties' in schema:
                properties = schema['properties']
                for key in properties:
                    property = properties[key]
                    tuple_with_definition = tuple_type(
                        field=key,
                        filter=self.FILTERS_BASED_ON_FIELD_TYPE[property['type']],
                        type=property['type']
                    )
                    list_of_tuple_with_definitions.append(tuple_with_definition)
            else:
                logger.info('There are no properties provided in schema from that benefit plan')
        else:
            logger.info('There is no schema provided in benefit plan')
