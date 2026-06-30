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
        self.assertIn("номер пять тысяч восемьсот девяносто два", result)
        self.assertIn("тысяча четыреста девяносто девять рублей", result)
        self.assertIn("двадцать седьмого января", result)
        self.assertIn("четырнадцати ноль ноль", result)
        self.assertIn("восемнадцати ноль ноль", result)

    def test_number_sign_reads_as_normal_cardinal(self):
        """№ before a number should expand to 'номер' + normal cardinal, not digit-by-digit."""
        result = normalize("заказ №5892")
        self.assertIn("номер пять тысяч", result)
        self.assertNotIn("пять восемь девять два", result)

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


if __name__ == "__main__":
    unittest.main()
