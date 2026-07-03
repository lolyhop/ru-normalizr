"""
Domain-specific normalization tests for restaurant booking / Yandex Direct bot scenarios.
Based on real production examples.
"""
import unittest

from ru_normalizr import normalize


class OrderNumberTests(unittest.TestCase):
    """Numbers following order/identifier context words are read digit-by-digit."""

    def test_8_digit_order_number_after_nomer_zakaza(self):
        self.assertEqual(
            normalize("Ваш номер заказа 12345678"),
            "Ваш номер заказа один два три четыре пять шесть семь восемь",
        )

    def test_4_digit_order_number_after_zakaz(self):
        self.assertEqual(
            normalize("Ваш заказ 1234 принят"),
            "Ваш заказ один два три четыре принят",
        )

    def test_9_digit_article_number_after_artikul(self):
        self.assertEqual(
            normalize("Артикул 987654321"),
            "Артикул девять восемь семь шесть пять четыре три два один",
        )

    def test_4_digit_number_after_kod(self):
        self.assertEqual(
            normalize("Код 1234"),
            "Код один два три четыре",
        )

    def test_order_amount_is_not_read_digit_by_digit_when_followed_by_rubles(self):
        """'заказа' triggers identifier context but currency unit overrides it."""
        self.assertEqual(
            normalize("Сумма заказа 1500 рублей"),
            "Сумма заказа тысяча пятьсот рублей",
        )

    def test_order_amount_not_digit_by_digit_when_followed_by_abbreviated_rubles(self):
        self.assertEqual(
            normalize("Стоимость заказа 2000 руб."),
            "Стоимость заказа две тысячи рублей",
        )


class DateNormalizationTests(unittest.TestCase):
    """Various date formats encountered in booking confirmations."""

    def test_text_date_with_month_name_and_year(self):
        self.assertEqual(
            normalize("Бронирование на 15 января 2024"),
            "Бронирование на пятнадцатого января две тысячи двадцать четвёртого года",
        )

    def test_full_numeric_date_with_dot_separator(self):
        result = normalize("02.05.2023")
        self.assertIn("второго мая", result)
        self.assertIn("две тысячи двадцать третьего", result)

    def test_full_numeric_date_with_dash_separator(self):
        result = normalize("02-05-2023")
        self.assertIn("второго мая", result)
        self.assertIn("две тысячи двадцать третьего", result)

    def test_partial_date_without_year(self):
        self.assertEqual(
            normalize("02.05"),
            "второго мая",
        )

    def test_partial_date_zero_padded_day_and_month(self):
        self.assertEqual(
            normalize("09.11"),
            "девятого ноября",
        )

    def test_date_range_s_po_with_month_name(self):
        result = normalize("с 3 по 7 января")
        self.assertIn("третьего", result)
        self.assertIn("седьмое", result)
        self.assertIn("января", result)

    def test_decimal_number_not_confused_with_partial_date(self):
        """'2.7' should NOT become 'второго июля' — single-digit month has no leading zero."""
        result = normalize("2.7 км")
        self.assertNotIn("июля", result)
        self.assertNotIn("февраля", result)


class TimeNormalizationTests(unittest.TestCase):
    """Time expressions common in booking confirmations."""

    def test_colon_time_in_sentence(self):
        result = normalize("столик на 2 персоны в 19:00")
        self.assertIn("девятнадцать", result)
        self.assertIn("ноль ноль", result)

    def test_space_separated_time_with_nonzero_minutes(self):
        result = normalize("В 6 30 ожидаем вас")
        self.assertIn("шесть", result)
        self.assertIn("тридцать", result)

    def test_space_separated_time_with_zero_minutes(self):
        """'в 7 00' — must render 'ноль ноль', not just 'семь'."""
        result = normalize("в 7 00 ровно")
        self.assertIn("семь", result)
        self.assertIn("ноль ноль", result)

    def test_space_separated_time_v_prep(self):
        result = normalize("Встречаемся в 14 30")
        self.assertIn("четырнадцать", result)
        self.assertIn("тридцать", result)


class MoneyNormalizationTests(unittest.TestCase):
    """Currency amounts in restaurant/bot contexts."""

    def test_rubli_abbreviated(self):
        self.assertEqual(
            normalize("Стоимость 1500 руб."),
            "Стоимость тысяча пятьсот рублей",
        )

    def test_rubli_full_genitive_form(self):
        self.assertEqual(
            normalize("Сумма заказа 1000 рублей"),
            "Сумма заказа тысяча рублей",
        )

    def test_one_thousand_rubles_drops_odna_prefix(self):
        """'одна тысяча рублей' → 'тысяча рублей'."""
        result = normalize("стоимость 1000 руб.")
        self.assertIn("тысяча рублей", result)
        self.assertNotIn("одна тысяча", result)

    def test_decimal_rubles_formats_as_rubles_and_kopecks(self):
        self.assertEqual(
            normalize("Итого 3.50 рублей"),
            "Итого три рубля пятьдесят копеек",
        )

    def test_decimal_rubles_zero_kopecks_omitted(self):
        result = normalize("Итого 5.00 рублей")
        self.assertIn("пять рублей", result)
        self.assertNotIn("ноль копеек", result)

    def test_dollars_abbreviated_accusative_case(self):
        result = normalize("иметь 1000 долл.")
        self.assertIn("тысячу долларов", result)

    def test_no_trailing_period_after_money_unit(self):
        result = normalize("сумму 100 тыс. долл.")
        self.assertFalse(
            result.endswith("долларов."),
            f"Expected no trailing period, got: {result!r}",
        )


class OrderDeliveryTests(unittest.TestCase):
    """Full delivery-notification sentences combining multiple normalization features."""

    def test_full_delivery_notification(self):
        result = normalize(
            "Ваш заказ №5892 на сумму 1 499 руб. будет доставлен 27.01.2025 с 14:00 до 18:00"
        )
        self.assertIn("номер пять восемь девять два", result)
        self.assertIn("тысяча четыреста девяносто девять рублей", result)
        self.assertIn("двадцать седьмого января", result)
        self.assertIn("четырнадцати ноль ноль", result)
        self.assertIn("восемнадцати ноль ноль", result)

    def test_number_sign_reads_digit_by_digit(self):
        """№ before a number should expand to 'номер' + digit-by-digit reading."""
        result = normalize("Ваш заказ №12345")
        self.assertIn("номер один два три четыре пять", result)

    def test_na_summu_uses_nominative(self):
        """'на сумму X рублей' should render X in nominative, not accusative."""
        result = normalize("на сумму 1499 руб.")
        self.assertIn("тысяча", result)
        self.assertNotIn("тысячу", result)


class OrdinalSuffixTests(unittest.TestCase):
    """Ordinal suffix forms in context."""

    def test_dative_ordinal_suffix_mu_matches_noun(self):
        """'5-му маршруту' — dative suffix 'му' should give dative ordinal."""
        self.assertEqual(
            normalize("Курьер едет по 5-му маршруту"),
            "Курьер едет по пятому маршруту",
        )

    def test_feminine_nominative_ordinal_not_overridden_by_genitive_noun(self):
        """'10-я в очереди' — 'я' suffix means feminine nominative; 'очереди' (genitive) must not override."""
        result = normalize("Позиция 10-я в очереди")
        self.assertIn("десятая", result)

    def test_instrumental_ordinal_suffix_ym_with_noun(self):
        """'1ым номером' — instrumental suffix 'ым' should match 'номером' (instrumental)."""
        result = normalize("1ым номером")
        self.assertIn("первым", result)


class AddressKorpusTests(unittest.TestCase):
    """'Korpus' (building block) notation in delivery addresses."""

    def test_glued_house_korpus(self):
        self.assertEqual(normalize("Дом 15к1"), "Дом пятнадцать корпус один")

    def test_hyphenated_house_korpus(self):
        self.assertEqual(normalize("Дом 15-к1"), "Дом пятнадцать корпус один")

    def test_spaced_glued_house_korpus(self):
        self.assertEqual(normalize("дом 15 к1"), "дом пятнадцать корпус один")

    def test_korpus_abbreviation_with_period_after_comma(self):
        self.assertEqual(normalize("Дом 15, к. 1"), "Дом пятнадцать, корпус один")

    def test_korp_abbreviation_with_period(self):
        self.assertEqual(normalize("дом 15 корп. 2"), "дом пятнадцать корпус два")

    def test_korp_abbreviation_without_period(self):
        self.assertEqual(normalize("дом 15, корп 2"), "дом пятнадцать, корпус два")

    def test_spaced_korpus_needs_address_context(self):
        """A bare 'N к N' without an address anchor is a ratio, not a korpus."""
        result = normalize("Ставки 5 к 3 в пользу фаворита")
        self.assertIn("пять к трём", result)

    def test_preposition_k_with_time_not_treated_as_korpus(self):
        result = normalize("к 18:00 мы приедем")
        self.assertNotIn("корпус", result)

    def test_dative_preposition_k_before_plain_number_unaffected(self):
        result = normalize("обратитесь к 5 специалистам")
        self.assertIn("к пяти специалистам", result)


class AddressAbbreviationTests(unittest.TestCase):
    """Common Russian address abbreviations expanded before a number."""

    def test_dom_abbreviation(self):
        result = normalize("д. 15к2")
        self.assertIn("дом пятнадцать", result)

    def test_kvartira_abbreviation_with_period(self):
        self.assertEqual(normalize("кв. 12"), "квартира двенадцать")

    def test_kvartira_abbreviation_without_period(self):
        result = normalize("дом 5к2, кв 34")
        self.assertIn("квартира тридцать четыре", result)

    def test_square_meters_not_confused_with_apartment(self):
        """'кв м'/'кв. м' (square meters) must stay a unit, not become 'квартира'."""
        self.assertEqual(normalize("5 кв м"), "пять квадратных метров")
        self.assertEqual(normalize("5 кв. м"), "пять квадратных метров")

    def test_full_address_with_all_components(self):
        result = normalize("ул. Ленина, д. 5, корп. 2, кв. 34")
        self.assertIn("улица Ленина", result)
        self.assertIn("дом пять", result)
        self.assertIn("корпус два", result)
        self.assertIn("квартира тридцать четыре", result)

    def test_stroenie_expands_with_address_context(self):
        result = normalize("дом 5, стр. 2")
        self.assertIn("строение два", result)

    def test_stroenie_without_period_with_address_context(self):
        result = normalize("дом 5 стр 2")
        self.assertIn("строение два", result)

    def test_str_page_reference_unaffected_by_address_rules(self):
        """'стр. N' without an address anchor still means 'страница' (page)."""
        self.assertEqual(
            normalize("см. рис. 2 и табл. 3, стр. 4"),
            "смотри рисунок два и таблица три, страница четыре",
        )


class AddressHouseLetterTests(unittest.TestCase):
    """House-number letter suffixes (е.g. '15Б', '5Е') kept as a literal letter, not dropped."""

    def test_uppercase_house_letter_hyphenated(self):
        result = normalize("Улица 15Б")
        self.assertIn("пятнадцать Б", result)

    def test_lowercase_house_letter_glued(self):
        result = normalize("дом 15а")
        self.assertNotEqual(result, "дом пятнадцать")

    def test_house_letter_e_not_confused_with_ordinal_suffix(self):
        """Uppercase 'Е' is a house letter ('дом 5Е'); lowercase '5-е' is an ordinal."""
        result_house = normalize("Дом 5Е")
        self.assertNotIn("пятое", result_house)
        self.assertIn("пять Е", result_house)
        result_ordinal = normalize("В 1990-е годы")
        self.assertIn("девяностые", result_ordinal)


class AddressSlashAndStroenieTests(unittest.TestCase):
    """House number with slash-separated liter/korpus ('123/1') and glued
    'стр' notation ('5стр1'), common in RU/BY address formats."""

    def test_slash_house_liter_with_street_context(self):
        result = normalize("Гродно, улица Дзержинского, 123/1")
        self.assertIn("сто двадцать три дробь один", result)

    def test_slash_house_liter_with_abbreviated_street(self):
        result = normalize("ул. Дзержинского, 5/2")
        self.assertIn("пять дробь два", result)

    def test_slash_with_dom_and_apartment(self):
        result = normalize("д. 10/2, кв. 5")
        self.assertIn("дом десять дробь два", result)
        self.assertIn("квартира пять", result)

    def test_math_fraction_unaffected_without_address_context(self):
        """'3/4 стакана' is a cooking fraction, not a house number."""
        self.assertEqual(normalize("3/4 стакана муки"), "три четвёртых стакана муки")

    def test_ratio_fraction_unaffected_without_address_context(self):
        self.assertEqual(normalize("скидка 1/2 от суммы"), "скидка одна вторая от суммы")

    def test_glued_stroenie_notation(self):
        result = normalize("дом 5стр1")
        self.assertIn("строение один", result)


if __name__ == "__main__":
    unittest.main()
