# Version Management Strategy - RAG System

**Document Owner:** Kira Preston - Senior Technical Project Manager  
**Created:** August 4, 2025  
**Status:** Active  

## 📋 Overview

This document defines the comprehensive version management strategy for the RAG System, including semantic versioning, branching strategy, release procedures, and maintenance workflows.

## 🏷️ Semantic Versioning Scheme

### Version Format: `MAJOR.MINOR.PATCH`

**Format**: `X.Y.Z` (e.g., `1.0.0`, `1.2.3`, `2.0.0`)

#### MAJOR Version (X.Y.Z → X+1.0.0)
**Incremented for breaking changes that require user intervention**

**Triggers:**
- API breaking changes (endpoint removal, response format changes)
- Database schema changes requiring migration
- Configuration format changes requiring user action
- Architecture changes affecting deployment procedures
- Dependency changes requiring system updates

**Examples:**
- `1.5.2 → 2.0.0`: Major UI overhaul requiring new configuration
- `2.3.1 → 3.0.0`: API v2 removal, migration to v3 required

#### MINOR Version (X.Y.Z → X.Y+1.0)
**Incremented for new features and enhancements**

**Triggers:**
- New document format support (Excel, PowerPoint)
- New API endpoints or functionality
- UI feature additions (dark mode, advanced search)
- Performance improvements and optimizations
- Security enhancements and hardening
- Backward-compatible dependency updates

**Examples:**
- `1.0.0 → 1.1.0`: OCR support for image-based PDFs
- `1.2.0 → 1.3.0`: Multi-language document processing

#### PATCH Version (X.Y.Z → X.Y.Z+1)
**Incremented for bug fixes and maintenance**

**Triggers:**
- Bug fixes and stability improvements
- Security patches and vulnerability fixes
- Performance optimizations without new features
- Documentation updates and corrections
- Configuration adjustments and improvements
- Dependency security updates

**Examples:**
- `1.1.0 → 1.1.1`: Fix document upload progress bar
- `1.2.3 → 1.2.4`: Security patch for PDF processing

### Pre-Release Versions

#### Alpha Releases: `X.Y.Z-alpha.N`
- **Purpose**: Early development builds for internal testing
- **Stability**: Unstable, breaking changes expected
- **Usage**: Development and initial feature validation
- **Example**: `1.2.0-alpha.1`, `1.2.0-alpha.2`

#### Beta Releases: `X.Y.Z-beta.N`
- **Purpose**: Feature-complete builds for testing
- **Stability**: Feature-complete but may contain bugs
- **Usage**: User acceptance testing and feedback
- **Example**: `1.2.0-beta.1`, `1.2.0-beta.2`

#### Release Candidates: `X.Y.Z-rc.N`
- **Purpose**: Production-ready candidates for final validation
- **Stability**: Production-ready pending final validation
- **Usage**: Final testing before production release
- **Example**: `1.2.0-rc.1`, `1.2.0-rc.2`

## 🌿 Branching Strategy

### Git Flow Model

#### Main Branches

**`main` Branch**
- **Purpose**: Production-ready code
- **Protection**: Protected, requires PR approval
- **Deployment**: Automatically deployed to production
- **Merge Policy**: Only from `release/*` and `hotfix/*` branches
- **Tagging**: All release tags applied here

**`develop` Branch**
- **Purpose**: Integration branch for active development
- **Protection**: Protected, requires PR approval
- **Deployment**: Deployed to staging environment
- **Merge Policy**: Feature branches merge here first
- **Testing**: Continuous integration and automated testing

#### Supporting Branches

**Feature Branches: `feature/description`**
- **Purpose**: New feature development
- **Naming**: `feature/pdf-ocr-support`, `feature/dark-mode`
- **Lifecycle**: Created from `develop`, merged back to `develop`
- **Duration**: Short-lived (1-2 weeks maximum)
- **Testing**: Must pass all tests before merge

**Release Branches: `release/X.Y.Z`**
- **Purpose**: Prepare new production releases
- **Naming**: `release/1.2.0`, `release/2.0.0`
- **Lifecycle**: Created from `develop`, merged to `main` and `develop`
- **Activities**: Final testing, bug fixes, version preparation
- **Duration**: 1 week for MINOR/PATCH, 2 weeks for MAJOR

**Hotfix Branches: `hotfix/X.Y.Z`**
- **Purpose**: Critical production fixes
- **Naming**: `hotfix/1.1.1`, `hotfix/1.2.4`
- **Lifecycle**: Created from `main`, merged to `main` and `develop`
- **Priority**: Highest priority, can interrupt other work
- **Duration**: 24-48 hours maximum

### Branch Protection Rules

#### `main` Branch Protection
- Require pull request reviews (2 approvers)
- Require status checks to pass
- Require branches to be up to date
- Restrict push to administrators only
- Include administrators in restrictions

#### `develop` Branch Protection
- Require pull request reviews (1 approver)
- Require status checks to pass
- Allow merge commits, squash merging disabled
- Delete head branches after merge

## 🚀 Release Procedures

### Major Release Process (X.0.0)

#### Phase 1: Planning (4 weeks before)
1. **Feature Freeze**: Complete all planned features
2. **Documentation Review**: Update all user and technical docs
3. **Breaking Change Assessment**: Document all breaking changes
4. **Migration Guide Creation**: Prepare upgrade procedures
5. **Stakeholder Communication**: Notify users of upcoming changes

#### Phase 2: Release Preparation (2 weeks before)
1. **Create Release Branch**: `git checkout -b release/X.0.0 develop`
2. **Version Updates**: Update version numbers in all files
3. **Release Notes**: Complete comprehensive release notes
4. **Testing Suite**: Execute full regression test suite
5. **Security Audit**: Complete security review and vulnerability scan

#### Phase 3: Release Execution (Release day)
1. **Final Testing**: Last-minute validation on release branch
2. **Merge to Main**: `git checkout main && git merge release/X.0.0`
3. **Create Tag**: `git tag -a vX.0.0 -m "Release vX.0.0"`
4. **Deploy Production**: Execute production deployment
5. **Post-Release**: Merge back to develop, delete release branch

### Minor Release Process (X.Y.0)

#### Phase 1: Preparation (1 week before)
1. **Feature Integration**: Ensure all features merged to develop
2. **Testing Validation**: Run automated test suite
3. **Documentation Updates**: Update feature documentation
4. **Release Notes**: Prepare feature changelog

#### Phase 2: Release (Release day)
1. **Create Release Branch**: `git checkout -b release/X.Y.0 develop`
2. **Version Bump**: Update version numbers
3. **Final Testing**: Quick regression test
4. **Merge and Tag**: Merge to main, create tag
5. **Deploy**: Production deployment

### Patch Release Process (X.Y.Z)

#### Hotfix Procedure (Critical fixes)
1. **Create Hotfix Branch**: `git checkout -b hotfix/X.Y.Z main`
2. **Implement Fix**: Make minimal necessary changes
3. **Test Fix**: Validate fix resolves issue without regression
4. **Merge to Main**: `git checkout main && git merge hotfix/X.Y.Z`
5. **Tag Release**: `git tag -a vX.Y.Z -m "Hotfix vX.Y.Z"`
6. **Deploy**: Immediate production deployment
7. **Backport**: Merge hotfix to develop branch

#### Regular Patch Procedure
1. **Accumulate Fixes**: Collect bug fixes in develop
2. **Create Release Branch**: When ready for patch release
3. **Follow Minor Process**: Use simplified minor release process

## 🏷️ Release Tagging Standards

### Tag Naming Convention
- **Format**: `vX.Y.Z` (with 'v' prefix)
- **Examples**: `v1.0.0`, `v1.2.3`, `v2.0.0-beta.1`

### Tag Creation
```bash
# Lightweight tag (not recommended for releases)
git tag vX.Y.Z

# Annotated tag (recommended for releases)
git tag -a vX.Y.Z -m "Release version X.Y.Z"

# Tag with detailed message
git tag -a vX.Y.Z -m "Release version X.Y.Z

Major features:
- Feature A implementation
- Feature B enhancement
- Critical bug fixes

Breaking changes:
- API endpoint changes
- Configuration updates"
```

### Tag Management
```bash
# List all tags
git tag -l

# Show tag details
git show vX.Y.Z

# Push tags to remote
git push origin vX.Y.Z
git push origin --tags

# Delete tag (if needed)
git tag -d vX.Y.Z
git push origin --delete vX.Y.Z
```

## 📅 Release Schedule

### Regular Release Cycle

#### Quarterly Major/Minor Releases
- **Q1 Release**: March 1st (Major/Minor)
- **Q2 Release**: June 1st (Minor)
- **Q3 Release**: September 1st (Minor)
- **Q4 Release**: December 1st (Major/Minor)

#### Monthly Patch Releases
- **First Monday**: Regular patch releases
- **As Needed**: Critical hotfixes (24-48 hour turnaround)

### Release Calendar Template

#### 6 Weeks Before Release
- [ ] Feature freeze for next release
- [ ] Begin release planning and documentation
- [ ] Security audit and vulnerability assessment

#### 4 Weeks Before Release
- [ ] Create release branch
- [ ] Begin comprehensive testing
- [ ] Finalize release notes and documentation

#### 2 Weeks Before Release
- [ ] Complete testing and bug fixes
- [ ] Final documentation review
- [ ] Stakeholder notification

#### 1 Week Before Release
- [ ] Final validation and sign-off
- [ ] Prepare deployment procedures
- [ ] Release candidate creation

#### Release Day
- [ ] Execute release procedures
- [ ] Deploy to production
- [ ] Monitor system health
- [ ] Update documentation sites

## 📊 Version Tracking

### File Locations for Version Numbers

#### Application Code
```python
# app/main.py
app = FastAPI(
    title="Local RAG System API",
    description="Fully local RAG system with ChromaDB and Ollama",
    version="1.0.0"  # UPDATE HERE
)
```

#### Package Configuration
```python
# app/reflex_app/rag_reflex_app/rag_reflex_app.py
# Version displayed in UI
app_version = "1.0.0"  # UPDATE HERE
```

#### Docker Configuration
```yaml
# docker-compose.production.yml
services:
  rag-backend:
    image: rag-system:1.0.0  # UPDATE HERE
    labels:
      - "version=1.0.0"      # UPDATE HERE
```

#### Documentation
```markdown
# docs/user_manual.md
**Version:** 1.0.0  # UPDATE HERE
**Last Updated:** August 4, 2025
```

### Automated Version Management

#### Version Update Script
```bash
#!/bin/bash
# scripts/update_version.sh

NEW_VERSION=$1
if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

# Update version in main.py
sed -i "s/version=\".*\"/version=\"$NEW_VERSION\"/" app/main.py

# Update version in UI
sed -i "s/app_version = \".*\"/app_version = \"$NEW_VERSION\"/" app/reflex_app/rag_reflex_app/rag_reflex_app.py

# Update Docker compose
sed -i "s/rag-system:.*/rag-system:$NEW_VERSION/" docker-compose.production.yml

echo "Version updated to $NEW_VERSION"
```

## 🔄 Hotfix and Patch Management

### Hotfix Criteria
Immediate hotfixes required for:
- **Security vulnerabilities**: Any security issues
- **Data loss**: Issues causing document or query data loss
- **System unavailability**: Critical system failures
- **Performance degradation**: >50% performance reduction

### Hotfix Procedure
1. **Assess Impact**: Determine scope and urgency
2. **Create Hotfix Branch**: From main branch
3. **Implement Fix**: Minimal necessary changes only
4. **Test**: Focused testing on fix area
5. **Deploy**: Emergency deployment procedure
6. **Monitor**: Enhanced monitoring post-deployment
7. **Post-Mortem**: Root cause analysis and prevention

### Patch Accumulation
- **Bug Fix Threshold**: Accumulate 3-5 bug fixes
- **Security Updates**: Monthly dependency updates
- **Documentation**: Include doc fixes in patches
- **Performance**: Minor optimizations and improvements

## 📈 Release Metrics and Success Criteria

### Release Health Metrics

#### Technical Metrics
- **Deployment Success Rate**: >95%
- **Rollback Rate**: <5%
- **Critical Issues**: Zero critical issues within 24 hours
- **Performance Impact**: <10% performance degradation

#### Quality Metrics
- **Test Coverage**: Maintain >90% coverage
- **Documentation Completeness**: 100% API coverage
- **User Experience**: No regression in core workflows
- **Accessibility**: Maintain WCAG 2.1 AA compliance

### Success Criteria by Release Type

#### Major Release Success
- [ ] All breaking changes documented
- [ ] Migration procedures tested
- [ ] User training materials updated
- [ ] Performance benchmarks met
- [ ] Security audit completed

#### Minor Release Success
- [ ] New features fully functional
- [ ] Backward compatibility maintained
- [ ] Documentation updated
- [ ] No critical regressions
- [ ] User feedback collected

#### Patch Release Success
- [ ] Target issues resolved
- [ ] No new regressions introduced
- [ ] Deployment completed successfully
- [ ] System stability maintained
- [ ] Monitoring confirms fix

### Post-Release Monitoring

#### First 24 Hours
- **Enhanced Monitoring**: Extended logging and alerting
- **Performance Tracking**: Response times and resource usage
- **Error Monitoring**: New error patterns or spikes
- **User Feedback**: Support channels and user reports

#### First Week
- **Stability Assessment**: System health and performance trends
- **Feature Adoption**: Usage of new features (minor releases)
- **Issue Tracking**: Any emerging issues or patterns
- **Documentation Feedback**: User guide effectiveness

#### First Month
- **Success Evaluation**: Release success criteria review
- **Lessons Learned**: Process improvements for next release
- **User Satisfaction**: Feature satisfaction and adoption
- **Technical Debt**: Identify areas for future improvement

## 🛠️ Tools and Automation

### Git Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Run tests before commit
python -m pytest tests/
npm run lint
```

### Automated Workflows
- **CI/CD Pipeline**: GitHub Actions for testing and deployment
- **Version Validation**: Automated version consistency checks
- **Release Notes**: Automated changelog generation
- **Deployment**: Automated production deployment scripts

### Release Checklist Automation
- **Pre-release**: Automated testing and validation
- **Release**: Deployment and verification scripts
- **Post-release**: Monitoring and health check automation

---

## 📋 Release Checklist Template

### Pre-Release Checklist
- [ ] All planned features implemented and tested
- [ ] Version numbers updated in all files
- [ ] Release notes completed and reviewed
- [ ] Documentation updated and validated
- [ ] Security audit completed (Major/Minor)
- [ ] Performance benchmarks validated
- [ ] Backup procedures verified
- [ ] Rollback procedures tested

### Release Day Checklist
- [ ] Final regression testing completed
- [ ] Release branch merged to main
- [ ] Release tag created and pushed
- [ ] Production deployment executed
- [ ] System health verified post-deployment
- [ ] Release notes published
- [ ] Stakeholders notified
- [ ] Monitoring alerts configured

### Post-Release Checklist
- [ ] System monitoring for 24 hours
- [ ] User feedback collection initiated
- [ ] Support documentation updated
- [ ] Development branch updated
- [ ] Next release planning initiated
- [ ] Lessons learned documentation
- [ ] Release success metrics collected

---

This version management strategy ensures consistent, reliable, and predictable releases while maintaining high quality and system stability throughout the development lifecycle.