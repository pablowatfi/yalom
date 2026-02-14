
# Engineering Standards & Mandatory Code Adherence Guide

This document defines NON-NEGOTIABLE engineering standards for any automated or human contributor modifying this repository.

Any code change MUST comply with this document.

Failure to comply means the change is invalid.

---

# 1. Core Engineering Principles

## 1.1 Architectural Principles

All changes must follow:

- Single Responsibility Principle (SRP)
- Open/Closed Principle (OCP)
- Liskov Substitution Principle (LSP)
- Interface Segregation Principle (ISP)
- Dependency Inversion Principle (DIP)

Additionally:

- Prefer composition over inheritance
- Favor immutability
- Avoid hidden side effects
- Avoid tight coupling
- Explicit dependencies only
- No circular dependencies

---

## 1.2 Code Quality Standards

All code must be:

- Deterministic
- Readable
- Minimal
- Explicit
- Strictly typed (where supported)
- Free of dead code
- Free of commented-out legacy code
- Free of debugging artifacts
- Free of unused imports

---

# 2. Project Structure Rules

## 2.1 Clean Architecture Enforcement

Required structure:

/src
&nbsp;&nbsp;&nbsp;&nbsp;/domain          → Pure business logic (no external dependencies)
&nbsp;&nbsp;&nbsp;&nbsp;/application     → Use cases, orchestration
&nbsp;&nbsp;&nbsp;&nbsp;/infrastructure  → External systems (DB, APIs, filesystem, frameworks)
&nbsp;&nbsp;&nbsp;&nbsp;/interfaces      → Controllers, HTTP, CLI, UI

Rules:

- Domain must not depend on infrastructure.
- Infrastructure may depend inward.
- Interfaces must call application layer only.
- No business logic in controllers.
- No framework code in domain.

---

# 3. Code Style & Formatting

## 3.1 General Rules

- Follow language idiomatic standards.
- Prefer clarity over cleverness.
- Functions should generally not exceed ~40 lines.
- Classes must be cohesive and focused.
- Avoid deep nesting (>3 levels).
- No magic numbers (use named constants).
- No long parameter lists (>5).

## 3.2 Naming Conventions

Names must be:

- Descriptive and intention-revealing
- Not abbreviated unless industry standard
- Verb-based for functions (e.g., calculate_total)
- Noun-based for classes (e.g., PaymentProcessor)
- Boolean variables must read naturally (e.g., is_active, has_permission)

---

# 4. Typing & Contracts

- Use strict typing.
- Avoid dynamic or `any` types unless unavoidable.
- All public functions must define explicit input and output types.
- Validate inputs at system boundaries.
- Raise explicit exceptions.
- Never silently coerce types.

---

# 5. Error Handling

- Never swallow exceptions.
- Never use bare except.
- Use domain-specific exceptions.
- Fail fast.
- Log errors with context.
- Do not expose sensitive data in errors.
- No silent fallbacks.

---

# 6. Logging Standards

## 6.1 Logging Philosophy

Logs must be:

- Structured (JSON if applicable)
- Context-rich
- Machine-parsable
- Non-redundant
- Free of secrets

## 6.2 Logging Levels

- DEBUG → Diagnostic details
- INFO → High-level state changes
- WARNING → Recoverable issues
- ERROR → Failures requiring attention
- CRITICAL → System-level failure

## 6.3 Logging Rules

- No print statements.
- No console debugging.
- Include correlation IDs where applicable.
- Include request or session identifiers when relevant.
- Log at system boundaries.
- Do not log credentials, tokens, or sensitive data.

---

# 7. Dependency Management

- No unused dependencies.
- Prefer standard library over external packages.
- Avoid heavy frameworks if lightweight alternatives suffice.
- Lock dependency versions.
- All dependencies must be justified.
- No hidden transitive reliance.

---

# 8. Configuration Management

- No hardcoded secrets.
- No hardcoded environment-specific values.
- Use environment variables.
- Centralized configuration module.
- Fail explicitly on missing required config.

---

# 9. Security Standards

Mandatory:

- Validate all external input.
- Sanitize user-provided data.
- Avoid injection vulnerabilities.
- Principle of least privilege.
- No secrets in code.
- Do not log sensitive data.
- Validate and sanitize external responses.

---

# 10. Performance Standards

- Avoid premature optimization.
- Avoid obvious inefficiencies.
- Avoid N+1 patterns.
- Avoid repeated expensive computations.
- Cache when appropriate and safe.
- Benchmark before major performance changes.

---

# 11. API Design Standards

If modifying APIs:

- Follow RESTful conventions.
- Use consistent naming.
- Version APIs.
- Use proper HTTP status codes.
- Deterministic responses.
- Structured error responses.
- Do not introduce breaking changes silently.

---

# 12. Documentation Requirements

Every change must:

- Update relevant README sections.
- Document public interfaces.
- Add docstrings to public methods.
- Explain non-obvious decisions.
- Document architectural changes.

Docstrings must include:

- Purpose
- Inputs
- Outputs
- Exceptions raised

---

# 13. Refactoring Rules

When modifying existing code:

- Improve it if touching it.
- Reduce complexity.
- Remove duplication.
- Reduce cognitive load.
- Preserve backward compatibility unless explicitly instructed otherwise.

---

# 14. Concurrency & Async

If applicable:

- Avoid shared mutable state.
- Make concurrency explicit.
- Avoid blocking calls in async contexts.
- Document concurrency model.
- Use proper synchronization mechanisms.

---

# 15. Data Handling

- Use explicit schemas.
- No loosely structured payloads.
- Validate all external input.
- Avoid unsafe dictionary access.
- No silent schema evolution.

---

# 16. Observability

Changes must preserve or improve:

- Logging clarity
- Metrics hooks (if present)
- Traceability
- Error visibility

Never reduce observability.

---

# 17. Git & Change Hygiene

Each change must:

- Be atomic.
- Have a clear commit message.
- Avoid unrelated modifications.
- Avoid reformatting entire files unnecessarily.
- Avoid whitespace-only commits.

---

# 18. Prohibited Practices

Strictly forbidden:

- Global mutable state (unless explicitly justified)
- God objects
- Hidden side effects
- Silent fallbacks
- Catch-all exception handlers
- Hardcoded credentials
- Business logic inside controllers
- Debug statements left in code

---

# 19. Adding New Code

Before adding new functionality, verify:

- It does not duplicate existing logic.
- It belongs in the correct architectural layer.
- It has a single responsibility.
- It improves clarity.
- It is necessary.

---

# 20. Mandatory Self-Checklist

Before finalizing a change, verify:

- [ ] Code is minimal and readable
- [ ] Architecture boundaries are respected
- [ ] Errors are handled explicitly
- [ ] Logging is structured and safe
- [ ] Configuration is externalized
- [ ] Dependencies are justified
- [ ] Security risks are mitigated
- [ ] Performance is acceptable
- [ ] Documentation is updated

If any answer is "no", revise before committing.

---

# 21. Guiding Philosophy

Write code as if:

- It will be maintained for 10 years.
- It will run at scale.
- A security audit will review it.
- A new engineer must understand it quickly.
- It must never silently fail.

Clarity > cleverness
Correctness > speed of writing
Safety > convenience

---

End of adhere_code.md
