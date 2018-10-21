# -*- coding: utf-8 -*-

from decimal import Decimal
from koalixcrm.crm.documents.sales_document_position import SalesDocumentPosition


class Calculations:

    @staticmethod
    def calculate_document_price(document, pricing_date):
        """Performs a price recalculation on contact documents.
        The calculated price is stored in the last_calculated_price and last_calculated_tax.
        The date when the price was calculated is stored in last_pricing_date

        Args:
            document: possible document classes must be derived from Contract
            pricing_date: must be a python date object

        Returns:
            1 (Boolean) when passed
            or raises exception

        Raises:
            Can trow Product.NoPriceFound when Product Price could not be found"""

        price = 0
        tax = 0
        positions = SalesDocumentPosition.objects.filter(sales_document=document.id)
        contact_for_price_calculation = document.customer
        if positions.exists():
            for position in positions:
                price += Calculations.calculate_position_price(position,
                                                               pricing_date,
                                                               contact_for_price_calculation,
                                                               document.currency)
                tax += Calculations.calculate_position_tax(position, document.currency)

            if document.discount is not None:
                discount = Decimal(document.discount)
                total_price = price * (1 - discount / 100)
                total_tax = tax * (1 - discount / 100)
                price = int(total_price / document.currency.get_rounding()) * document.currency.get_rounding()
                tax = int(total_tax / document.currency.get_rounding()) * document.currency.get_rounding()
        document.last_calculated_price = price
        document.last_calculated_tax = tax
        document.last_pricing_date = pricing_date
        document.save()
        return 1

    @staticmethod
    def calculate_position_price(position, pricing_date, contact, currency):
        """Performs a price calculation a position.
        The calculated price is stored in the last_calculated_price
        The date when the price was calculated is stored in last_pricing_date

        Args:
            position: possible document classes must be derived from Contract class
            pricing_date: must be a python date object
            contact: is used for the lookup of the correct price
            currency: is used for the lookup of the correct price and for the definition of the rounding

        Returns:
            calculated price
            or raises exception

        Raises:
            Can trow Product.NoPriceFound when Product Price could not be found"""

        if not position.overwrite_product_price:
            position.position_price_per_unit = position.product_type.get_price(pricing_date,
                                                                               position.unit,
                                                                               contact,
                                                                               currency)
        nominal_total = position.position_price_per_unit * position.quantity
        if isinstance(position.discount, Decimal):
            nominal_minus_discount = nominal_total * (1 - position.discount / 100)
        else:
            nominal_minus_discount = nominal_total
        total_with_tax = nominal_minus_discount * ((100-position.product_type.get_tax_rate()) / 100)
        position.last_calculated_price = int(total_with_tax / currency.get_rounding()) * currency.get_rounding()
        position.last_pricing_date = pricing_date
        position.save()
        return position.last_calculated_price

    @staticmethod
    def calculate_position_tax(position, currency):
        """Performs a tax calculation a position.
        The calculated tax is stored in the last_calculated_tax

        Args:
            position: possible document classes must be derived from Position class
            currency: is used for the definition of the rounding

        Returns:
            calculated tax
            or raises exception

        Raises:
            Can trow Product.NoPriceFound when Product Price could not be found"""
        nominal_total = position.position_price_per_unit * position.quantity
        if isinstance(position.discount, Decimal):
            nominal_minus_discount = nominal_total * (1 - position.discount / 100)
        else:
            nominal_minus_discount = nominal_total
        total_tax = nominal_minus_discount * position.product_type.get_tax_rate() / 100
        position.last_calculated_tax = int(total_tax / currency.get_rounding()) * currency.get_rounding()
        position.save()
        return position.last_calculated_tax
