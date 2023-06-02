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

        :return: The type of the object.
        :rtype: str
        """
        return self.OBJECT_CLASS.__name__

    def load_definition(self, tuple_type: type, **kwargs) -> List[namedtuple]:
        """
        Load the definition of how to create filters.

        This method retrieves the definition of how to create filters and returns it as a list of named tuples.
        Each named tuple is built with the provided `tuple_type` and has the fields `field`, `filter`, and `value`.

        Example named tuple: <Type>(field=<str>, filter=<str>, value=<str>)
        Example usage: BenefitPlan(field='income', filter='lt, gte, icontains, exact', value='')

        :param tuple_type: The type of the named tuple.
        :type tuple_type: type

        :return: A list of named tuples representing the definition of how to create filters.
        :rtype: List[namedtuple]
        """
        list_of_tuple_with_definitions = []
        benefit_plan_id = kwargs.get('uuid', None)
        if benefit_plan_id:
            benefit_plan = BenefitPlan.objects.filter(id=benefit_plan_id).first()
            if benefit_plan:
                list_of_tuple_with_definitions.extend(self.__process_schema_and_build_tuple(benefit_plan, tuple_type))
            else:
                logger.warning('There is no benefit plan with such id')
        else:
            logger.warning('Id of benefit plan is not provided')
        return list_of_tuple_with_definitions

    def __process_schema_and_build_tuple(
        self,
        benefit_plan: BenefitPlan,
        tuple_type: type
    ) -> List[namedtuple]:
        tuples_with_definitions = []
        schema = benefit_plan.beneficiary_data_schema
        if schema and 'properties' in schema:
            properties = schema['properties']
            for key, value in properties.items():
                tuple_with_definition = tuple_type(
                    field=key,
                    filter=self.FILTERS_BASED_ON_FIELD_TYPE[value['type']],
                    type=value['type']
                )
                tuples_with_definitions.append(tuple_with_definition)
        else:
            logger.warning('Cannot retrieve definitions of filters based '
                           'on the provided schema due to either empty schema '
                           'or missing properties in schema file')
        return tuples_with_definitions
