#!/bin/bash
# Master Command Validation Runner
# Tests all 137 commands across 5 phases

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration  
export LOG_FILE="$PROJECT_ROOT/command_validation_$(date +%Y%m%d_%H%M%S).log"
export TEST_TIMEOUT=300
export VALIDATION_STRICT=true
export CLEANUP_AFTER_TEST=false

# Source the validation framework
source "$SCRIPT_DIR/lib/command_validator.sh"

# Change to project root
cd "$PROJECT_ROOT"

log "${BLUE}======================================${NC}"
log "${BLUE}RAG System Command Validation Started${NC}"
log "${BLUE}======================================${NC}"
log "${BLUE}Testing 137 commands across 5 phases${NC}"
log "${BLUE}Project Root: $PROJECT_ROOT${NC}"
log "${BLUE}Log File: $LOG_FILE${NC}"
log "${BLUE}Started: $(date)${NC}"

# Check system resources
check_system_resources

# Test phases in order
phases=(
    "prerequisites"
    "foundation" 
    "core_operations"
    "integration"
    "edge_cases"
)

phase_descriptions=(
    "System Prerequisites & Dependencies"
    "Foundation Setup & Core Services"
    "Core Operations & Basic Functionality"
    "Integration Testing & Advanced Features"
    "Edge Cases & Recovery Procedures"
)

total_phases=${#phases[@]}
current_phase=0

for i in "${!phases[@]}"; do
    phase="${phases[$i]}"
    description="${phase_descriptions[$i]}"
    current_phase=$((i + 1))
    
    log ""
    log "${BLUE}======================================${NC}"
    log "${BLUE}PHASE $current_phase/$total_phases: $description${NC}"
    log "${BLUE}======================================${NC}"
    
    phase_start_time=$(date +%s)
    
    if "$SCRIPT_DIR/validate_${phase}.sh"; then
        phase_end_time=$(date +%s)
        phase_duration=$((phase_end_time - phase_start_time))
        log "${GREEN}✅ Phase $current_phase/$total_phases PASSED${NC} (${phase_duration}s)"
    else
        phase_end_time=$(date +%s)
        phase_duration=$((phase_end_time - phase_start_time))
        log "${RED}❌ Phase $current_phase/$total_phases FAILED${NC} (${phase_duration}s)"
        
        # Ask user if they want to continue or abort
        if [[ "${VALIDATION_STRICT:-true}" == "true" ]]; then
            log "${RED}STRICT MODE: Aborting due to phase failure${NC}"
            exit 1
        else
            log "${YELLOW}CONTINUING despite phase failure...${NC}"
        fi
    fi
done

# Final summary and recommendations
log ""
log "${BLUE}======================================${NC}"
log "${BLUE}FINAL VALIDATION REPORT${NC}"
log "${BLUE}======================================${NC}"

# Calculate overall metrics
total_duration=$(( $(date +%s) - $(date -r "$LOG_FILE" +%s) ))
total_minutes=$((total_duration / 60))
total_seconds=$((total_duration % 60))

log "${BLUE}Total Duration:${NC} ${total_minutes}m ${total_seconds}s"

# Success criteria evaluation
if [ $TOTAL_COMMANDS -gt 0 ]; then
    success_rate=$(( PASSED_COMMANDS * 100 / TOTAL_COMMANDS ))
    
    if [ $FAILED_COMMANDS -eq 0 ]; then
        log "${GREEN}🎉 PERFECT SCORE: All commands passed!${NC}"
        log "${GREEN}✅ System is ready for production use${NC}"
    elif [ $success_rate -ge 95 ]; then
        log "${GREEN}🎉 EXCELLENT: ${success_rate}% success rate${NC}"
        log "${GREEN}✅ System is production ready with minor issues${NC}"
    elif [ $success_rate -ge 85 ]; then
        log "${YELLOW}⚠️  GOOD: ${success_rate}% success rate${NC}"
        log "${YELLOW}⚠️  Review failed commands before production deployment${NC}"
    else
        log "${RED}🚨 NEEDS ATTENTION: ${success_rate}% success rate${NC}"
        log "${RED}❌ System requires fixes before production use${NC}"
    fi
else
    log "${RED}❌ No commands were tested${NC}"
    exit 1
fi

# Recommendations based on results
log ""
log "${BLUE}=== RECOMMENDATIONS ===${NC}"

if [ $FAILED_COMMANDS -gt 0 ]; then
    log "${YELLOW}📋 TODO:${NC}"
    log "  1. Review failed commands in the log above"
    log "  2. Fix underlying issues (dependencies, configuration, etc.)"
    log "  3. Re-run validation: $0"
    log "  4. Consider running individual phase scripts for focused testing"
    log ""
    log "${BLUE}Individual Phase Scripts:${NC}"
    for phase in "${phases[@]}"; do
        log "  ./scripts/validate_${phase}.sh"
    done
fi

if [ $success_rate -ge 95 ]; then
    log "${GREEN}📋 NEXT STEPS:${NC}"
    log "  1. ✅ System validation completed successfully"
    log "  2. 🚀 Ready for production deployment"
    log "  3. 📊 Set up monitoring and health checks"
    log "  4. 📚 Review MASTER_DOCUMENTATION.md for usage guidance"
    log "  5. 🔄 Schedule regular validation runs"
fi

log ""
log "${BLUE}=== LOG FILE ===${NC}"
log "Complete validation log saved to: $LOG_FILE"
log "Review failed commands: grep '❌' $LOG_FILE"
log "Review warnings: grep '⚠️' $LOG_FILE"

log ""
log "${BLUE}Command Validation Completed: $(date)${NC}"

# Exit with appropriate code
if [ $FAILED_COMMANDS -eq 0 ]; then
    exit 0
else
    exit 1
fi