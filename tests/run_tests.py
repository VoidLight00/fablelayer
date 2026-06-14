"""tests/run_tests.py — 단일 진입점.

tests/test_*.py 전체를 unittest 로 발견·실행하고, 하나라도 실패하면 exit 1.
표준 라이브러리만 사용한다(외부 의존 0). fail-closed: 수집 에러(import 실패 등)도 실패로 본다.
"""

from __future__ import annotations

import os
import sys
import unittest

# 패키지 루트(<root>)를 import 경로에 넣어 `import fablelayer.*` 가 어디서 실행되든 동작하게 한다.
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_TESTS_DIR)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def main() -> int:
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=_TESTS_DIR, pattern="test_*.py", top_level_dir=_ROOT)

    # discover 가 import 에러를 _FailedTest 로 흡수할 수 있으므로 errors 도 fail 로 본다.
    if loader.errors:
        for err in loader.errors:
            sys.stderr.write(str(err) + "\n")
        return 1

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful() and not result.errors and not result.failures:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
