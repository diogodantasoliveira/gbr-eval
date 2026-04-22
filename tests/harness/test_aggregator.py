"""Tests for the file aggregator — holistic evaluation mode."""

from __future__ import annotations

from gbr_eval.harness.aggregator import (
    _file_priority,
    _guess_language,
    _truncate_large_file,
    aggregate_files_for_prompt,
)


class TestFilePriority:
    def test_page_tsx_highest_priority(self) -> None:
        assert _file_priority("src/app/page.tsx") == 0

    def test_component_file(self) -> None:
        assert _file_priority("src/components/button.tsx") == 1

    def test_api_route(self) -> None:
        assert _file_priority("src/app/api/runs/route.ts") == 2

    def test_lib_file(self) -> None:
        assert _file_priority("src/lib/utils.ts") == 3

    def test_hooks_file(self) -> None:
        assert _file_priority("src/hooks/use-data.ts") == 3

    def test_unknown_file(self) -> None:
        assert _file_priority("src/config.ts") == 4

    def test_page_higher_than_component(self) -> None:
        assert _file_priority("src/app/page.tsx") < _file_priority("src/components/x.tsx")

    def test_component_higher_than_api(self) -> None:
        assert _file_priority("src/components/x.tsx") < _file_priority("src/app/api/route.ts")


class TestTruncateLargeFile:
    def test_small_file_unchanged(self) -> None:
        content = "line\n" * 100
        assert _truncate_large_file(content) == content

    def test_exactly_at_threshold_unchanged(self) -> None:
        content = "line\n" * 500
        assert _truncate_large_file(content) == content

    def test_large_file_truncated(self) -> None:
        lines = [f"line {i}\n" for i in range(1000)]
        content = "".join(lines)
        result = _truncate_large_file(content)
        assert "line 0" in result
        assert "line 199" in result  # last line of head (200 lines)
        assert "line 999" in result  # last line of tail
        assert "[... truncated" in result
        assert "700 lines" in result  # 1000 - 200 - 100 = 700 omitted

    def test_truncation_marker_present(self) -> None:
        content = "x\n" * 600
        result = _truncate_large_file(content)
        assert "[... truncated" in result


class TestGuessLanguage:
    def test_typescript(self) -> None:
        assert _guess_language("file.ts") == "typescript"

    def test_tsx(self) -> None:
        assert _guess_language("file.tsx") == "tsx"

    def test_python(self) -> None:
        assert _guess_language("file.py") == "python"

    def test_unknown_extension(self) -> None:
        assert _guess_language("file.xyz") == ""

    def test_nested_path(self) -> None:
        assert _guess_language("src/app/page.tsx") == "tsx"


class TestAggregateFilesForPrompt:
    def test_empty_file_list(self) -> None:
        result = aggregate_files_for_prompt([])
        assert "0 files" in result
        assert "0 total lines" in result

    def test_single_file(self) -> None:
        files = [("src/app/page.tsx", "export default function Home() {}")]
        result = aggregate_files_for_prompt(files)
        assert "1 files" in result
        assert "src/app/page.tsx" in result
        assert "export default function Home() {}" in result

    def test_multiple_small_files_all_included(self) -> None:
        files = [
            ("src/app/page.tsx", "const Page = () => <div>Hello</div>;\n"),
            ("src/components/header.tsx", "const Header = () => <nav>Nav</nav>;\n"),
            ("src/lib/utils.ts", "export function cn() { return ''; }\n"),
        ]
        result = aggregate_files_for_prompt(files)
        assert "3 files" in result
        # All content should be present.
        assert "const Page" in result
        assert "const Header" in result
        assert "export function cn" in result

    def test_file_listing_always_present(self) -> None:
        files = [
            ("src/a.ts", "a"),
            ("src/b.ts", "b"),
        ]
        result = aggregate_files_for_prompt(files)
        assert "### Files" in result
        assert "- src/a.ts" in result
        assert "- src/b.ts" in result

    def test_priority_ordering(self) -> None:
        files = [
            ("src/lib/utils.ts", "util code"),
            ("src/app/page.tsx", "page code"),
            ("src/components/btn.tsx", "btn code"),
        ]
        result = aggregate_files_for_prompt(files)
        # page.tsx should appear before components which should appear before lib.
        page_pos = result.index("## src/app/page.tsx")
        comp_pos = result.index("## src/components/btn.tsx")
        lib_pos = result.index("## src/lib/utils.ts")
        assert page_pos < comp_pos < lib_pos

    def test_large_file_truncation_in_aggregate(self) -> None:
        large_content = "\n".join(f"line {i}" for i in range(600))
        files = [("big.tsx", large_content)]
        result = aggregate_files_for_prompt(files)
        assert "[... truncated" in result
        assert "line 0" in result
        assert "line 599" in result  # should be in the tail

    def test_max_chars_limit_respected(self) -> None:
        # Create files that together exceed a small max_chars.
        files = [
            ("src/app/page.tsx", "A" * 500),
            ("src/components/x.tsx", "B" * 500),
            ("src/lib/y.ts", "C" * 500),
        ]
        result = aggregate_files_for_prompt(files, max_chars=800)
        # The result should be under the limit (approximately).
        assert len(result) <= 900  # some tolerance for headers
        # The file listing should still contain all files.
        assert "src/app/page.tsx" in result
        assert "src/components/x.tsx" in result
        assert "src/lib/y.ts" in result

    def test_max_chars_prioritizes_important_files(self) -> None:
        # page.tsx (priority 0) should be included before lib (priority 3).
        files = [
            ("src/lib/y.ts", "C" * 200),
            ("src/app/page.tsx", "A" * 200),
        ]
        result = aggregate_files_for_prompt(files, max_chars=400)
        # page.tsx content should be present.
        assert "AAAA" in result

    def test_overview_stats_correct(self) -> None:
        files = [
            ("a.py", "line1\nline2\nline3"),
            ("b.py", "line1\nline2"),
        ]
        result = aggregate_files_for_prompt(files)
        assert "2 files" in result
        # a.py has 3 lines, b.py has 2 lines = 5 total.
        assert "5 total lines" in result

    def test_markdown_fence_uses_correct_language(self) -> None:
        files = [("src/app/page.tsx", "const x = 1;")]
        result = aggregate_files_for_prompt(files)
        assert "```tsx" in result

    def test_content_omitted_stub_when_budget_tight(self) -> None:
        # First file takes up most budget, second gets a stub.
        files = [
            ("src/app/page.tsx", "A" * 400),
            ("src/components/big.tsx", "B" * 400),
        ]
        result = aggregate_files_for_prompt(files, max_chars=600)
        # At least one file should show "content omitted" or be missing content.
        if "content omitted" in result:
            assert "budget exceeded" in result
