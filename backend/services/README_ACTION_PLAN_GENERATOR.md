# Action Plan Generator Service

## Overview

The `ActionPlanGenerator` service generates a comprehensive 7-day export readiness action plan based on an export readiness report. It prioritizes tasks based on dependencies, distributes them across 7 days with realistic timelines, and accounts for government processing times.

## Requirements

Implements requirements:
- **13.1**: 7-day action plan with specific tasks for each day
- **13.2**: Task prioritization based on dependencies
- **13.3**: Realistic task distribution (Day 1: GST LUT/HS code, Day 2-3: Certifications, Day 4-5: Documents, Day 6: Logistics, Day 7: Review)
- **13.5**: Account for government processing times
- **13.6**: Flag certifications requiring >7 days with interim steps

## Features

### Task Prioritization
- **Dependencies**: GST LUT before shipment, HS code confirmation before certifications
- **Critical certifications first**: High priority certifications scheduled before optional ones
- **Realistic timelines**: Tasks distributed based on actual processing times

### 7-Day Structure
1. **Day 1**: Foundation Setup - GST LUT, HS code confirmation, IEC verification, bank setup
2. **Day 2-3**: Certification Applications - Critical certifications prioritized
3. **Day 4-5**: Document Preparation - Commercial invoice, packing list, certificates
4. **Day 6**: Logistics Planning - Freight booking, customs broker, shipment tracking
5. **Day 7**: Final Review - Document review and readiness checklist

### Government Processing Times
- Accounts for realistic processing times for each task
- Flags certifications requiring >7 days with interim steps
- Provides clear guidance on what can be completed within 7 days

## Usage

### Basic Usage

```python
from action_plan_generator import ActionPlanGenerator
from models import ExportReadinessReport

# Initialize generator
generator = ActionPlanGenerator()

# Generate action plan from report
action_plan = generator.generate_plan(report)

# Access daily plans
for day in action_plan.days:
    print(f"Day {day.day}: {day.title}")
    for task in day.tasks:
        print(f"  - {task.title}")
```

### Example Output

```python
ActionPlan(
    days=[
        DayPlan(
            day=1,
            title="Foundation Setup - Documentation & Banking",
            tasks=[
                Task(
                    id="task_gst_lut",
                    title="Apply for GST LUT (Letter of Undertaking)",
                    description="Submit Letter of Undertaking to GST portal...",
                    category=TaskCategory.DOCUMENTATION,
                    estimated_duration="2-3 hours",
                    dependencies=[]
                ),
                # ... more tasks
            ]
        ),
        # ... days 2-7
    ],
    progress_percentage=0.0
)
```

## Task Templates

The service includes pre-defined task templates for common export activities:

### Foundational Tasks (Day 1)
- **GST LUT**: Letter of Undertaking for GST exemption
- **HS Code Confirmation**: Verify HS code with customs
- **IEC Verification**: Ensure Import Export Code is active
- **Bank Account Setup**: Set up EEFC account for export payments

### Certification Tasks (Day 2-3)
- Generated dynamically based on report certifications
- Prioritized by urgency (high → medium → low)
- Flagged if processing time exceeds 7 days

### Document Tasks (Day 4-5)
- **Document Preparation**: Commercial invoice, packing list, shipping bill
- **Certificate of Origin**: Apply for certificate from EPC/Chamber
- **Packaging Compliance**: Verify packaging and labeling requirements

### Logistics Tasks (Day 6)
- **Customs Broker**: Engage Customs House Agent (CHA)
- **Freight Booking**: Book shipping and arrange insurance
- **Shipment Tracking**: Set up tracking systems

### Final Review Tasks (Day 7)
- **Final Document Review**: Review all documents for accuracy
- **Readiness Checklist**: Complete export readiness verification

## Task Dependencies

The service automatically manages task dependencies:

```
GST LUT ──┐
          ├──> Document Preparation ──> Freight Booking ──> Final Review
HS Code ──┘                                                      ↑
                                                                 │
Certificate of Origin ───────────────────────────────────────────┘
```

## Handling Long Certifications

For certifications requiring >7 days:

```python
# Example: FDA Registration (30 days)
Task(
    id="task_cert_fda",
    title="Apply for FDA Registration (Interim Step - Full process exceeds 7 days)",
    description="Begin application process for FDA Registration. "
                "Note: Full certification takes 30 days. "
                "Complete initial documentation and submit application within 7 days. "
                "Follow up on approval status after submission.",
    category=TaskCategory.CERTIFICATION,
    estimated_duration="30 days",
    dependencies=["task_hs_code_confirmation"]
)
```

## Testing

Comprehensive unit tests cover:
- ✅ 7-day plan generation
- ✅ Task distribution across days
- ✅ Dependency management
- ✅ Priority-based certification ordering
- ✅ Long certification flagging
- ✅ Edge cases (no certifications, etc.)

Run tests:
```bash
pytest test_action_plan_generator.py -v
```

## Integration

### With Report Generator

```python
from report_generator import ReportGenerator
from action_plan_generator import ActionPlanGenerator

# Generate report
report_generator = ReportGenerator(rag_pipeline, llm_client)
report = report_generator.generate_report(query, hs_code, documents)

# Generate action plan
plan_generator = ActionPlanGenerator()
action_plan = plan_generator.generate_plan(report)

# Add to report
report.action_plan = action_plan
```

### With API Router

```python
from fastapi import APIRouter
from action_plan_generator import ActionPlanGenerator

router = APIRouter()
generator = ActionPlanGenerator()

@router.get("/api/action-plan/{report_id}")
async def get_action_plan(report_id: str):
    report = get_report_from_db(report_id)
    action_plan = generator.generate_plan(report)
    return action_plan
```

## Task Categories

Tasks are categorized for easy filtering and organization:

- `TaskCategory.DOCUMENTATION`: GST LUT, documents, certificates
- `TaskCategory.CERTIFICATION`: FDA, CE, REACH, BIS, ZED, SOFTEX
- `TaskCategory.LOGISTICS`: Freight, customs broker, tracking
- `TaskCategory.FINANCE`: Bank setup, working capital planning

## Progress Tracking

The action plan includes progress tracking:

```python
# Calculate progress
total_tasks = sum(len(day.tasks) for day in action_plan.days)
completed_tasks = sum(
    sum(1 for task in day.tasks if task.completed)
    for day in action_plan.days
)
progress = (completed_tasks / total_tasks) * 100

# Update action plan
action_plan.progress_percentage = progress
```

## Customization

### Adding Custom Tasks

```python
generator = ActionPlanGenerator()

# Add custom task template
generator.task_templates["custom_task"] = {
    "title": "Custom Task",
    "description": "Custom task description",
    "category": TaskCategory.DOCUMENTATION,
    "estimated_duration": "2 hours",
    "dependencies": ["task_gst_lut"],
}
```

### Modifying Day Distribution

Override `_distribute_tasks_across_days` method to customize task distribution logic.

## Best Practices

1. **Always generate from complete report**: Ensure the report has all certifications and requirements
2. **Update progress regularly**: Track task completion to show user progress
3. **Handle long certifications**: Clearly communicate when certifications exceed 7 days
4. **Respect dependencies**: Ensure dependent tasks are completed before proceeding
5. **Provide realistic timelines**: Use actual government processing times

## Error Handling

The service handles edge cases gracefully:

- **No certifications**: Generates plan with foundational, document, and logistics tasks
- **Empty days**: Adds placeholder tasks to ensure each day has at least one task
- **Invalid dependencies**: Validates dependency chains during generation

## Performance

- **Fast generation**: Typically completes in <100ms
- **Memory efficient**: Uses task templates to minimize memory usage
- **Scalable**: Can handle reports with many certifications

## Future Enhancements

Potential improvements:
- Dynamic day count (flexible 5-10 day plans)
- Machine learning for timeline prediction
- Integration with calendar systems
- Automated task reminders
- Progress analytics and insights

## Related Services

- `ReportGenerator`: Generates export readiness reports
- `CertificationSolver`: Provides detailed certification guidance
- `FinanceModule`: Calculates working capital and timelines
- `LogisticsRiskShield`: Analyzes logistics risks

## Support

For issues or questions:
1. Check unit tests for usage examples
2. Review task templates in `_initialize_task_templates()`
3. Consult design document for requirements details
