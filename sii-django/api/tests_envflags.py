from django.test import SimpleTestCase

from api.envflags import as_bool, resolver_debug


class EnvFlagsTests(SimpleTestCase):
    def test_as_bool_no_trata_false_como_true(self):
        self.assertFalse(as_bool("False"))
        self.assertFalse(as_bool("false"))
        self.assertFalse(as_bool("0"))
        self.assertTrue(as_bool("True"))
        self.assertTrue(as_bool("1"))
        self.assertFalse(as_bool(None, default=False))
        self.assertTrue(as_bool(None, default=True))

    def test_debug_apagado_en_vercel_production(self):
        self.assertFalse(resolver_debug("production", "True"))
        self.assertFalse(resolver_debug("production", "1"))
        self.assertFalse(resolver_debug("production", None))

    def test_debug_local_y_preview_respetan_la_variable(self):
        self.assertTrue(resolver_debug(None, "True"))
        self.assertFalse(resolver_debug(None, "False"))
        self.assertTrue(resolver_debug("preview", "true"))
        self.assertFalse(resolver_debug("preview", "false"))
        self.assertFalse(resolver_debug(None, None))
