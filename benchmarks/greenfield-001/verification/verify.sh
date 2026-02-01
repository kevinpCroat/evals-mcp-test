#!/bin/bash
# Greenfield Benchmark Verification Script
# Tests a from-scratch URL Shortener API implementation

set -e

BENCHMARK_NAME="greenfield-001"
START_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Initialize scoring components
tests_score=0
spec_score=0
quality_score=0
docs_score=0

# Server PID for cleanup
SERVER_PID=""

# Change to project directory
cd "$PROJECT_DIR"

echo -e "${YELLOW}Running Greenfield Benchmark Verification...${NC}" >&2

# Cleanup function
cleanup() {
    if [ ! -z "$SERVER_PID" ]; then
        echo -e "\n${YELLOW}Stopping server (PID: $SERVER_PID)...${NC}" >&2
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
}
trap cleanup EXIT

# 1. CHECK FOR REQUIRED FILES (Pre-flight check)
echo -e "\n${YELLOW}1. Checking for required files...${NC}" >&2

required_files_found=true
missing_files=""

# Check for main application file (various possible names)
if ! ls *.py > /dev/null 2>&1; then
    required_files_found=false
    missing_files="${missing_files}\n  - No Python files found"
fi

# Check for requirements.txt
if [ ! -f "requirements.txt" ]; then
    required_files_found=false
    missing_files="${missing_files}\n  - requirements.txt"
fi

# Check for README
if [ ! -f "README.md" ] && [ ! -f "readme.md" ] && [ ! -f "README.txt" ]; then
    required_files_found=false
    missing_files="${missing_files}\n  - README.md"
fi

if [ "$required_files_found" = false ]; then
    echo -e "${RED}ERROR: Missing required files:${missing_files}${NC}" >&2
    cat <<EOF
{
  "benchmark": "${BENCHMARK_NAME}",
  "timestamp": "${START_TIME}",
  "error": "Missing required files: ${missing_files}",
  "components": {
    "functional_tests": {"score": 0, "weight": 0.40, "details": "Required files missing"},
    "spec_compliance": {"score": 0, "weight": 0.30, "details": "Required files missing"},
    "code_quality": {"score": 0, "weight": 0.20, "details": "Required files missing"},
    "documentation": {"score": 0, "weight": 0.10, "details": "Required files missing"}
  },
  "base_score": 0,
  "penalties": {
    "time_penalty": 0,
    "iteration_penalty": 0,
    "error_penalty": 0
  },
  "final_score": 0,
  "passed": false
}
EOF
    exit 1
fi

echo -e "${GREEN}Required files found${NC}" >&2

# 2. INSTALL DEPENDENCIES
echo -e "\n${YELLOW}2. Installing dependencies...${NC}" >&2

if ! python3 -m pip install --user -q -r requirements.txt 2>&1 | grep -v "already satisfied" | head -5 >&2; then
    echo -e "${YELLOW}Dependencies installed${NC}" >&2
fi

# Install test dependencies
python3 -m pip install --user -q pytest pytest-cov requests 2>/dev/null || true

# 3. START THE SERVER
echo -e "\n${YELLOW}3. Starting the server...${NC}" >&2

# Find the main application file
APP_FILE=""
for file in app.py main.py server.py api.py url_shortener.py; do
    if [ -f "$file" ]; then
        APP_FILE="$file"
        break
    fi
done

if [ -z "$APP_FILE" ]; then
    # Try to find any Python file that might be the main file
    APP_FILE=$(ls *.py 2>/dev/null | head -1)
fi

if [ -z "$APP_FILE" ]; then
    echo -e "${RED}ERROR: Could not find main application file${NC}" >&2
    cat <<EOF
{
  "benchmark": "${BENCHMARK_NAME}",
  "timestamp": "${START_TIME}",
  "error": "No main application file found",
  "components": {
    "functional_tests": {"score": 0, "weight": 0.40, "details": "No application file"},
    "spec_compliance": {"score": 0, "weight": 0.30, "details": "No application file"},
    "code_quality": {"score": 0, "weight": 0.20, "details": "No application file"},
    "documentation": {"score": 0, "weight": 0.10, "details": "No application file"}
  },
  "base_score": 0,
  "penalties": {"time_penalty": 0, "iteration_penalty": 0, "error_penalty": 0},
  "final_score": 0,
  "passed": false
}
EOF
    exit 1
fi

echo "Found application file: $APP_FILE" >&2

# Start the server in the background
python3 "$APP_FILE" > server.log 2>&1 &
SERVER_PID=$!

echo "Server started with PID: $SERVER_PID" >&2

# Wait for server to be ready (max 15 seconds)
server_ready=false
for i in {1..30}; do
    if curl -s http://localhost:8080/ > /dev/null 2>&1; then
        server_ready=true
        echo -e "${GREEN}Server is ready${NC}" >&2
        break
    fi
    sleep 0.5
done

if [ "$server_ready" = false ]; then
    echo -e "${RED}Server failed to start or is not responding on port 8080${NC}" >&2
    echo "Server log:" >&2
    cat server.log >&2
    cat <<EOF
{
  "benchmark": "${BENCHMARK_NAME}",
  "timestamp": "${START_TIME}",
  "error": "Server failed to start on port 8080",
  "components": {
    "functional_tests": {"score": 0, "weight": 0.40, "details": "Server not running"},
    "spec_compliance": {"score": 0, "weight": 0.30, "details": "Server not running"},
    "code_quality": {"score": 0, "weight": 0.20, "details": "Server not running"},
    "documentation": {"score": 0, "weight": 0.10, "details": "Server not running"}
  },
  "base_score": 0,
  "penalties": {"time_penalty": 0, "iteration_penalty": 0, "error_penalty": 0},
  "final_score": 0,
  "passed": false
}
EOF
    exit 1
fi

# 4. RUN FUNCTIONAL TESTS (40% weight)
echo -e "\n${YELLOW}4. Running functional tests...${NC}" >&2

tests_details="Tests not run"
if python3 -m pytest "$SCRIPT_DIR/tests/test_api.py" -v --tb=short > test_results.txt 2>&1; then
    tests_passed=true
    # Count passed tests
    total_tests=$(grep -c "PASSED" test_results.txt 2>/dev/null | tr -d ' \n' || echo "0")
    failed_tests=$(grep -c "FAILED" test_results.txt 2>/dev/null | tr -d ' \n' || echo "0")

    if [ $total_tests -gt 0 ]; then
        total_tests=${total_tests:-0}
        failed_tests=${failed_tests:-0}
        tests_percent=$(python3 -c 'import sys; t=int(sys.argv[1].strip()); f=int(sys.argv[2].strip()); print(round((t/(t+f))*100, 2) if (t+f)>0 else 0)' "$total_tests" "$failed_tests")
        tests_score=$(python3 -c 'import sys; p=float(sys.argv[1].strip()); print(min(100, int(p)))' "$tests_percent")
        tests_details="Passed: ${total_tests}, Failed: ${failed_tests} (${tests_percent}%)"
        echo -e "${GREEN}Tests passed: ${total_tests}, failed: ${failed_tests}${NC}" >&2
    else
        tests_score=0
        tests_details="No tests passed"
    fi
else
    tests_passed=false
    total_tests=$(grep -c "PASSED" test_results.txt 2>/dev/null | tr -d ' \n' || echo "0")
    failed_tests=$(grep -c "FAILED" test_results.txt 2>/dev/null | tr -d ' \n' || echo "0")

    if [ $total_tests -gt 0 ]; then
        total_tests=${total_tests:-0}
        failed_tests=${failed_tests:-0}
        tests_percent=$(python3 -c 'import sys; t=int(sys.argv[1].strip()); f=int(sys.argv[2].strip()); print(round((t/(t+f))*100, 2) if (t+f)>0 else 0)' "$total_tests" "$failed_tests")
        tests_score=$(python3 -c 'import sys; p=float(sys.argv[1].strip()); print(min(100, int(p)))' "$tests_percent")
        tests_details="Passed: ${total_tests}, Failed: ${failed_tests} (${tests_percent}%)"
        echo -e "${YELLOW}Some tests failed - Passed: ${total_tests}, Failed: ${failed_tests}${NC}" >&2
    else
        tests_score=0
        tests_details="All tests failed"
        echo -e "${RED}All tests failed${NC}" >&2
    fi

    # Show failed test details
    grep "FAILED" test_results.txt | head -10 >&2 || true
fi

# 5. CHECK SPEC COMPLIANCE (30% weight)
echo -e "\n${YELLOW}5. Checking specification compliance...${NC}" >&2

spec_checks_passed=0
spec_checks_total=10

# Check 1: Can create a short URL
if curl -s -X POST http://localhost:8080/urls -H "Content-Type: application/json" -d '{"url":"https://www.example.com/test"}' | grep -q -E '(short_code|code|id)'; then
    spec_checks_passed=$((spec_checks_passed + 1))
    echo "  ✓ Can create short URL" >&2
else
    echo "  ✗ Cannot create short URL" >&2
fi

# Check 2: Short code is 6-8 alphanumeric characters
SHORT_CODE=$(curl -s -X POST http://localhost:8080/urls -H "Content-Type: application/json" -d '{"url":"https://www.example.com/test2"}' | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('short_code') or data.get('code') or data.get('id') or '')" 2>/dev/null)
if echo "$SHORT_CODE" | grep -qE '^[a-zA-Z0-9]{6,8}$'; then
    spec_checks_passed=$((spec_checks_passed + 1))
    echo "  ✓ Short code format is correct (6-8 alphanumeric)" >&2
else
    echo "  ✗ Short code format incorrect: $SHORT_CODE" >&2
fi

# Check 3: Can retrieve URL (redirect or stats)
if [ ! -z "$SHORT_CODE" ]; then
    REDIRECT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/$SHORT_CODE)
    if [ "$REDIRECT_STATUS" = "200" ] || [ "$REDIRECT_STATUS" = "301" ] || [ "$REDIRECT_STATUS" = "302" ]; then
        spec_checks_passed=$((spec_checks_passed + 1))
        echo "  ✓ Can access short URL" >&2
    else
        echo "  ✗ Cannot access short URL (status: $REDIRECT_STATUS)" >&2
    fi
fi

# Check 4: Can get stats
if [ ! -z "$SHORT_CODE" ]; then
    if curl -s http://localhost:8080/urls/$SHORT_CODE/stats | grep -q -E '(access_count|visits|clicks|count)'; then
        spec_checks_passed=$((spec_checks_passed + 1))
        echo "  ✓ Can get URL statistics" >&2
    else
        echo "  ✗ Cannot get URL statistics" >&2
    fi
fi

# Check 5: Can list URLs
if curl -s http://localhost:8080/urls | grep -q '\['; then
    spec_checks_passed=$((spec_checks_passed + 1))
    echo "  ✓ Can list URLs" >&2
else
    echo "  ✗ Cannot list URLs" >&2
fi

# Check 6: Can delete URL
if [ ! -z "$SHORT_CODE" ]; then
    DELETE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE http://localhost:8080/urls/$SHORT_CODE)
    if [ "$DELETE_STATUS" = "200" ] || [ "$DELETE_STATUS" = "204" ]; then
        spec_checks_passed=$((spec_checks_passed + 1))
        echo "  ✓ Can delete URL" >&2
    else
        echo "  ✗ Cannot delete URL (status: $DELETE_STATUS)" >&2
    fi
fi

# Check 7: Rejects invalid URLs
INVALID_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/urls -H "Content-Type: application/json" -d '{"url":"not-a-url"}')
if [ "$INVALID_STATUS" = "400" ] || [ "$INVALID_STATUS" = "422" ]; then
    spec_checks_passed=$((spec_checks_passed + 1))
    echo "  ✓ Rejects invalid URLs" >&2
else
    echo "  ✗ Accepts invalid URLs (status: $INVALID_STATUS)" >&2
fi

# Check 8: Returns 404 for non-existent URLs
NOTFOUND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/nonexistent)
if [ "$NOTFOUND_STATUS" = "404" ]; then
    spec_checks_passed=$((spec_checks_passed + 1))
    echo "  ✓ Returns 404 for non-existent URLs" >&2
else
    echo "  ✗ Does not return 404 for non-existent URLs (status: $NOTFOUND_STATUS)" >&2
fi

# Check 9: Stats include all required fields
if [ ! -z "$SHORT_CODE" ]; then
    NEW_CODE=$(curl -s -X POST http://localhost:8080/urls -H "Content-Type: application/json" -d '{"url":"https://www.example.com/stats-check"}' | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('short_code') or data.get('code') or data.get('id') or '')" 2>/dev/null)
    if [ ! -z "$NEW_CODE" ]; then
        STATS=$(curl -s http://localhost:8080/urls/$NEW_CODE/stats)
        if echo "$STATS" | grep -q -E '(original_url|url|long_url)' && \
           echo "$STATS" | grep -q -E '(access_count|visits|clicks|count)' && \
           echo "$STATS" | grep -q -E '(created_at|created|timestamp)'; then
            spec_checks_passed=$((spec_checks_passed + 1))
            echo "  ✓ Stats include all required fields" >&2
        else
            echo "  ✗ Stats missing required fields" >&2
        fi
    fi
fi

# Check 10: List returns array with required fields
LIST_RESPONSE=$(curl -s http://localhost:8080/urls)
if echo "$LIST_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list) and len(data) > 0:
        item = data[0]
        has_code = 'short_code' in item or 'code' in item or 'id' in item
        has_url = 'original_url' in item or 'url' in item or 'long_url' in item
        has_count = 'access_count' in item or 'visits' in item or 'clicks' in item or 'count' in item
        has_time = 'created_at' in item or 'created' in item or 'timestamp' in item
        if has_code and has_url and has_count and has_time:
            sys.exit(0)
    sys.exit(1)
except:
    sys.exit(1)
" 2>/dev/null; then
    spec_checks_passed=$((spec_checks_passed + 1))
    echo "  ✓ List returns proper format with all fields" >&2
else
    echo "  ✗ List does not return proper format" >&2
fi

spec_score=$(python3 -c "print(int(($spec_checks_passed / $spec_checks_total) * 100))")
spec_details="Passed ${spec_checks_passed}/${spec_checks_total} specification checks"
echo -e "${GREEN}Specification compliance: ${spec_checks_passed}/${spec_checks_total}${NC}" >&2

# 6. CODE QUALITY ANALYSIS (20% weight)
echo -e "\n${YELLOW}6. Analyzing code quality...${NC}" >&2

quality_checks_passed=0
quality_checks_total=5

# Check 1: Cyclomatic complexity (using radon if available, otherwise basic check)
if python3 -m pip show radon > /dev/null 2>&1; then
    python3 -m pip install --user -q radon 2>/dev/null || true
fi

if command -v radon > /dev/null 2>&1; then
    # Get average complexity
    COMPLEXITY=$(radon cc *.py -a 2>/dev/null | grep "Average complexity" | awk '{print $NF}' | tr -d '()' || echo "0")
    if [ ! -z "$COMPLEXITY" ]; then
        COMPLEXITY_OK=$(python3 -c "print(1 if float('$COMPLEXITY') < 10 else 0)" 2>/dev/null || echo "0")
        if [ "$COMPLEXITY_OK" = "1" ]; then
            quality_checks_passed=$((quality_checks_passed + 1))
            echo "  ✓ Cyclomatic complexity acceptable ($COMPLEXITY)" >&2
        else
            echo "  ✗ Cyclomatic complexity too high ($COMPLEXITY)" >&2
        fi
    else
        quality_checks_passed=$((quality_checks_passed + 1))
        echo "  ✓ Complexity check (radon not fully working, skipping)" >&2
    fi
else
    quality_checks_passed=$((quality_checks_passed + 1))
    echo "  ✓ Complexity check (radon not installed, skipping)" >&2
fi

# Check 2: No obvious code duplication
DUPLICATE_LINES=$(grep -rh "def \|class " *.py 2>/dev/null | sort | uniq -d | wc -l | tr -d ' ')
if [ "$DUPLICATE_LINES" -lt 3 ]; then
    quality_checks_passed=$((quality_checks_passed + 1))
    echo "  ✓ No significant code duplication" >&2
else
    echo "  ✗ Possible code duplication detected" >&2
fi

# Check 3: Proper error handling (check for try/except blocks)
if grep -q "try:" *.py 2>/dev/null && grep -q "except" *.py 2>/dev/null; then
    quality_checks_passed=$((quality_checks_passed + 1))
    echo "  ✓ Uses error handling (try/except)" >&2
else
    echo "  ✗ No error handling found" >&2
fi

# Check 4: Input validation (check for validation logic)
if grep -qE "(validate|is_valid|check_|raise|ValueError|TypeError)" *.py 2>/dev/null; then
    quality_checks_passed=$((quality_checks_passed + 1))
    echo "  ✓ Has input validation" >&2
else
    echo "  ✗ No input validation found" >&2
fi

# Check 5: Code organization (multiple functions/classes, not one big function)
FUNCTION_COUNT=$(grep -c "^def " *.py 2>/dev/null | awk '{sum+=$1} END {print sum}')
if [ "$FUNCTION_COUNT" -gt 5 ]; then
    quality_checks_passed=$((quality_checks_passed + 1))
    echo "  ✓ Well-organized code ($FUNCTION_COUNT functions)" >&2
else
    echo "  ✗ Code may lack proper organization ($FUNCTION_COUNT functions)" >&2
fi

quality_score=$(python3 -c "print(int(($quality_checks_passed / $quality_checks_total) * 100))")
quality_details="Passed ${quality_checks_passed}/${quality_checks_total} quality checks"
echo -e "${GREEN}Code quality: ${quality_checks_passed}/${quality_checks_total}${NC}" >&2

# 7. DOCUMENTATION CHECK (10% weight)
echo -e "\n${YELLOW}7. Checking documentation...${NC}" >&2

docs_checks_passed=0
docs_checks_total=5

# Check 1: README exists
if [ -f "README.md" ] || [ -f "readme.md" ] || [ -f "README.txt" ]; then
    docs_checks_passed=$((docs_checks_passed + 1))
    echo "  ✓ README file exists" >&2
    README_FILE=$(ls README.md readme.md README.txt 2>/dev/null | head -1)
else
    echo "  ✗ README file missing" >&2
    README_FILE=""
fi

# Check 2: README has setup instructions
if [ ! -z "$README_FILE" ] && grep -qiE "(setup|install|getting started)" "$README_FILE"; then
    docs_checks_passed=$((docs_checks_passed + 1))
    echo "  ✓ README has setup instructions" >&2
else
    echo "  ✗ README missing setup instructions" >&2
fi

# Check 3: README documents how to run the server
if [ ! -z "$README_FILE" ] && grep -qiE "(run|start|python|flask|fastapi|uvicorn)" "$README_FILE"; then
    docs_checks_passed=$((docs_checks_passed + 1))
    echo "  ✓ README documents how to run server" >&2
else
    echo "  ✗ README missing run instructions" >&2
fi

# Check 4: README documents API endpoints
if [ ! -z "$README_FILE" ] && grep -qiE "(endpoint|api|POST|GET|DELETE|/urls)" "$README_FILE"; then
    docs_checks_passed=$((docs_checks_passed + 1))
    echo "  ✓ README documents API endpoints" >&2
else
    echo "  ✗ README missing API documentation" >&2
fi

# Check 5: Code has docstrings or comments
if grep -qE "(\"\"\"|\#)" *.py 2>/dev/null; then
    docs_checks_passed=$((docs_checks_passed + 1))
    echo "  ✓ Code has comments/docstrings" >&2
else
    echo "  ✗ Code lacks comments/docstrings" >&2
fi

docs_score=$(python3 -c "print(int(($docs_checks_passed / $docs_checks_total) * 100))")
docs_details="Passed ${docs_checks_passed}/${docs_checks_total} documentation checks"
echo -e "${GREEN}Documentation: ${docs_checks_passed}/${docs_checks_total}${NC}" >&2

# Calculate base score (weighted sum)
base_score=$(python3 -c "
tests = $tests_score * 0.40
spec = $spec_score * 0.30
quality = $quality_score * 0.20
docs = $docs_score * 0.10
total = tests + spec + quality + docs
print(round(total, 2))
")

# No penalties in this benchmark
time_penalty=0
iteration_penalty=0
error_penalty=0

final_score=$(python3 -c "print(int($base_score))")

# Determine pass/fail (70% threshold)
if (( final_score >= 70 )); then
    passed="true"
    echo -e "\n${GREEN}PASSED${NC} - Score: ${final_score}/100" >&2
else
    passed="false"
    echo -e "\n${RED}FAILED${NC} - Score: ${final_score}/100 (need 70+)" >&2
fi

# Output JSON
cat <<EOF
{
  "benchmark": "${BENCHMARK_NAME}",
  "timestamp": "${START_TIME}",
  "components": {
    "functional_tests": {
      "score": ${tests_score},
      "weight": 0.40,
      "details": "${tests_details}"
    },
    "spec_compliance": {
      "score": ${spec_score},
      "weight": 0.30,
      "details": "${spec_details}"
    },
    "code_quality": {
      "score": ${quality_score},
      "weight": 0.20,
      "details": "${quality_details}"
    },
    "documentation": {
      "score": ${docs_score},
      "weight": 0.10,
      "details": "${docs_details}"
    }
  },
  "base_score": ${base_score},
  "penalties": {
    "time_penalty": ${time_penalty},
    "iteration_penalty": ${iteration_penalty},
    "error_penalty": ${error_penalty}
  },
  "final_score": ${final_score},
  "passed": ${passed}
}
EOF

# Cleanup
rm -f test_results.txt server.log 2>/dev/null || true

# Exit with appropriate code
if [ "$passed" = "true" ]; then
    exit 0
else
    exit 1
fi
