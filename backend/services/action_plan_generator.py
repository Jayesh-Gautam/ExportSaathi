"""
Action Plan Generator Service

This service generates a 7-day export readiness action plan based on the export readiness report.
It prioritizes tasks based on dependencies, distributes them across 7 days with realistic timelines,
and accounts for government processing times.

Requirements: 13.1, 13.2, 13.3, 13.5, 13.6
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Set
from datetime import datetime
from models import (
    ExportReadinessReport,
    ActionPlan,
    DayPlan,
    Task,
    TaskCategory,
    Certification,
    Priority,
)


class ActionPlanGenerator:
    """
    Generates 7-day action plans for export readiness.
    
    The generator prioritizes tasks based on:
    - Dependencies (GST LUT before shipment, critical certifications first)
    - Government processing times
    - Realistic daily workload distribution
    """
    
    def __init__(self):
        """Initialize the action plan generator."""
        # Define standard task templates
        self.task_templates = self._initialize_task_templates()
        
    def _initialize_task_templates(self) -> Dict[str, Dict]:
        """Initialize standard task templates."""
        return {
            "gst_lut": {
                "title": "Apply for GST LUT (Letter of Undertaking)",
                "description": "Submit Letter of Undertaking to GST portal for export without paying IGST. Required before first shipment.",
                "category": TaskCategory.DOCUMENTATION,
                "estimated_duration": "2-3 hours",
                "dependencies": [],
            },
            "hs_code_confirmation": {
                "title": "Confirm HS Code with Customs",
                "description": "Verify the predicted HS code with customs authorities to avoid classification disputes.",
                "category": TaskCategory.DOCUMENTATION,
                "estimated_duration": "1-2 hours",
                "dependencies": [],
            },
            "iec_verification": {
                "title": "Verify IEC (Import Export Code)",
                "description": "Ensure your IEC is active and updated with current business details.",
                "category": TaskCategory.DOCUMENTATION,
                "estimated_duration": "1 hour",
                "dependencies": [],
            },
            "bank_account_setup": {
                "title": "Set up Export Bank Account",
                "description": "Open or verify EEFC (Export Earners Foreign Currency) account for receiving export payments.",
                "category": TaskCategory.FINANCE,
                "estimated_duration": "2-3 hours",
                "dependencies": [],
            },
            "document_preparation": {
                "title": "Prepare Export Documents",
                "description": "Generate and validate commercial invoice, packing list, and shipping bill.",
                "category": TaskCategory.DOCUMENTATION,
                "estimated_duration": "3-4 hours",
                "dependencies": ["task_gst_lut", "task_hs_code_confirmation"],
            },
            "certificate_of_origin": {
                "title": "Apply for Certificate of Origin",
                "description": "Obtain Certificate of Origin from Export Promotion Council or Chamber of Commerce.",
                "category": TaskCategory.DOCUMENTATION,
                "estimated_duration": "2-3 hours",
                "dependencies": ["task_hs_code_confirmation"],
            },
            "freight_booking": {
                "title": "Book Freight and Logistics",
                "description": "Compare freight forwarders, book shipping, and arrange cargo insurance.",
                "category": TaskCategory.LOGISTICS,
                "estimated_duration": "3-4 hours",
                "dependencies": ["task_document_preparation"],
            },
            "customs_broker": {
                "title": "Engage Customs House Agent (CHA)",
                "description": "Select and engage a CHA for customs clearance and documentation support.",
                "category": TaskCategory.LOGISTICS,
                "estimated_duration": "2 hours",
                "dependencies": [],
            },
            "packaging_compliance": {
                "title": "Verify Packaging and Labeling",
                "description": "Ensure packaging meets destination country requirements and includes proper labeling.",
                "category": TaskCategory.LOGISTICS,
                "estimated_duration": "2-3 hours",
                "dependencies": [],
            },
            "final_review": {
                "title": "Final Document Review",
                "description": "Review all documents for accuracy, consistency, and compliance before shipment.",
                "category": TaskCategory.DOCUMENTATION,
                "estimated_duration": "2 hours",
                "dependencies": ["task_document_preparation", "task_certificate_of_origin"],
            },
            "shipment_tracking": {
                "title": "Set up Shipment Tracking",
                "description": "Configure tracking systems and prepare for customs clearance at destination.",
                "category": TaskCategory.LOGISTICS,
                "estimated_duration": "1 hour",
                "dependencies": ["task_freight_booking"],
            },
        }
    
    def generate_plan(self, report: ExportReadinessReport) -> ActionPlan:
        """
        Generate a 7-day action plan from an export readiness report.
        
        Args:
            report: The export readiness report containing certifications, timeline, and requirements
            
        Returns:
            ActionPlan with tasks distributed across 7 days
            
        The plan follows this structure:
        - Day 1: GST LUT, HS code confirmation, IEC verification, bank setup
        - Day 2-3: Critical certification applications
        - Day 4-5: Document preparation and certificates
        - Day 6: Logistics planning and freight booking
        - Day 7: Final review and readiness check
        """
        # Collect all tasks
        all_tasks: List[Task] = []
        
        # Add standard foundational tasks (Day 1)
        all_tasks.extend(self._generate_foundational_tasks())
        
        # Add certification tasks (Day 2-3)
        all_tasks.extend(self._generate_certification_tasks(report.certifications))
        
        # Add document preparation tasks (Day 4-5)
        all_tasks.extend(self._generate_document_tasks(report))
        
        # Add logistics tasks (Day 6)
        all_tasks.extend(self._generate_logistics_tasks(report))
        
        # Add final review tasks (Day 7)
        all_tasks.extend(self._generate_final_review_tasks())
        
        # Distribute tasks across 7 days based on dependencies and priorities
        day_plans = self._distribute_tasks_across_days(all_tasks, report)
        
        # Create action plan
        action_plan = ActionPlan(
            days=day_plans,
            progress_percentage=0.0
        )
        
        return action_plan
    
    def _generate_foundational_tasks(self) -> List[Task]:
        """Generate foundational tasks for Day 1."""
        tasks = []
        
        # GST LUT - highest priority
        tasks.append(Task(
            id="task_gst_lut",
            title=self.task_templates["gst_lut"]["title"],
            description=self.task_templates["gst_lut"]["description"],
            category=self.task_templates["gst_lut"]["category"],
            estimated_duration=self.task_templates["gst_lut"]["estimated_duration"],
            dependencies=self.task_templates["gst_lut"]["dependencies"],
        ))
        
        # HS Code confirmation
        tasks.append(Task(
            id="task_hs_code_confirmation",
            title=self.task_templates["hs_code_confirmation"]["title"],
            description=self.task_templates["hs_code_confirmation"]["description"],
            category=self.task_templates["hs_code_confirmation"]["category"],
            estimated_duration=self.task_templates["hs_code_confirmation"]["estimated_duration"],
            dependencies=self.task_templates["hs_code_confirmation"]["dependencies"],
        ))
        
        # IEC verification
        tasks.append(Task(
            id="task_iec_verification",
            title=self.task_templates["iec_verification"]["title"],
            description=self.task_templates["iec_verification"]["description"],
            category=self.task_templates["iec_verification"]["category"],
            estimated_duration=self.task_templates["iec_verification"]["estimated_duration"],
            dependencies=self.task_templates["iec_verification"]["dependencies"],
        ))
        
        # Bank account setup
        tasks.append(Task(
            id="task_bank_account_setup",
            title=self.task_templates["bank_account_setup"]["title"],
            description=self.task_templates["bank_account_setup"]["description"],
            category=self.task_templates["bank_account_setup"]["category"],
            estimated_duration=self.task_templates["bank_account_setup"]["estimated_duration"],
            dependencies=self.task_templates["bank_account_setup"]["dependencies"],
        ))
        
        return tasks
    
    def _generate_certification_tasks(self, certifications: List[Certification]) -> List[Task]:
        """Generate certification application tasks for Day 2-3."""
        tasks = []
        
        # Sort certifications by priority (high first)
        sorted_certs = sorted(
            certifications,
            key=lambda c: (
                0 if c.priority == Priority.HIGH else 1 if c.priority == Priority.MEDIUM else 2,
                c.estimated_timeline_days
            )
        )
        
        for cert in sorted_certs:
            # Check if certification requires >7 days
            if cert.estimated_timeline_days > 7:
                # Create interim step task
                task_description = (
                    f"Begin application process for {cert.name}. "
                    f"Note: Full certification takes {cert.estimated_timeline_days} days. "
                    f"Complete initial documentation and submit application within 7 days. "
                    f"Follow up on approval status after submission."
                )
                interim_note = " (Interim Step - Full process exceeds 7 days)"
            else:
                task_description = (
                    f"Apply for {cert.name} certification. "
                    f"Estimated timeline: {cert.estimated_timeline_days} days. "
                    f"Ensure all required documents are prepared and submitted."
                )
                interim_note = ""
            
            tasks.append(Task(
                id=f"task_cert_{cert.id}",
                title=f"Apply for {cert.name}{interim_note}",
                description=task_description,
                category=TaskCategory.CERTIFICATION,
                estimated_duration=f"{cert.estimated_timeline_days} days",
                dependencies=["task_hs_code_confirmation"],  # Certifications need HS code
            ))
        
        return tasks
    
    def _generate_document_tasks(self, report: ExportReadinessReport) -> List[Task]:
        """Generate document preparation tasks for Day 4-5."""
        tasks = []
        
        # Document preparation
        tasks.append(Task(
            id="task_document_preparation",
            title=self.task_templates["document_preparation"]["title"],
            description=self.task_templates["document_preparation"]["description"],
            category=self.task_templates["document_preparation"]["category"],
            estimated_duration=self.task_templates["document_preparation"]["estimated_duration"],
            dependencies=self.task_templates["document_preparation"]["dependencies"],
        ))
        
        # Certificate of Origin
        tasks.append(Task(
            id="task_certificate_of_origin",
            title=self.task_templates["certificate_of_origin"]["title"],
            description=self.task_templates["certificate_of_origin"]["description"],
            category=self.task_templates["certificate_of_origin"]["category"],
            estimated_duration=self.task_templates["certificate_of_origin"]["estimated_duration"],
            dependencies=self.task_templates["certificate_of_origin"]["dependencies"],
        ))
        
        # Packaging compliance
        tasks.append(Task(
            id="task_packaging_compliance",
            title=self.task_templates["packaging_compliance"]["title"],
            description=self.task_templates["packaging_compliance"]["description"],
            category=self.task_templates["packaging_compliance"]["category"],
            estimated_duration=self.task_templates["packaging_compliance"]["estimated_duration"],
            dependencies=self.task_templates["packaging_compliance"]["dependencies"],
        ))
        
        return tasks
    
    def _generate_logistics_tasks(self, report: ExportReadinessReport) -> List[Task]:
        """Generate logistics tasks for Day 6."""
        tasks = []
        
        # Customs broker
        tasks.append(Task(
            id="task_customs_broker",
            title=self.task_templates["customs_broker"]["title"],
            description=self.task_templates["customs_broker"]["description"],
            category=self.task_templates["customs_broker"]["category"],
            estimated_duration=self.task_templates["customs_broker"]["estimated_duration"],
            dependencies=self.task_templates["customs_broker"]["dependencies"],
        ))
        
        # Freight booking
        tasks.append(Task(
            id="task_freight_booking",
            title=self.task_templates["freight_booking"]["title"],
            description=self.task_templates["freight_booking"]["description"],
            category=self.task_templates["freight_booking"]["category"],
            estimated_duration=self.task_templates["freight_booking"]["estimated_duration"],
            dependencies=self.task_templates["freight_booking"]["dependencies"],
        ))
        
        # Shipment tracking setup
        tasks.append(Task(
            id="task_shipment_tracking",
            title=self.task_templates["shipment_tracking"]["title"],
            description=self.task_templates["shipment_tracking"]["description"],
            category=self.task_templates["shipment_tracking"]["category"],
            estimated_duration=self.task_templates["shipment_tracking"]["estimated_duration"],
            dependencies=self.task_templates["shipment_tracking"]["dependencies"],
        ))
        
        return tasks
    
    def _generate_final_review_tasks(self) -> List[Task]:
        """Generate final review tasks for Day 7."""
        tasks = []
        
        # Final document review
        tasks.append(Task(
            id="task_final_review",
            title=self.task_templates["final_review"]["title"],
            description=self.task_templates["final_review"]["description"],
            category=self.task_templates["final_review"]["category"],
            estimated_duration=self.task_templates["final_review"]["estimated_duration"],
            dependencies=self.task_templates["final_review"]["dependencies"],
        ))
        
        # Export readiness checklist
        tasks.append(Task(
            id="task_readiness_checklist",
            title="Complete Export Readiness Checklist",
            description="Review all completed tasks, verify document accuracy, and confirm readiness for first shipment.",
            category=TaskCategory.DOCUMENTATION,
            estimated_duration="1-2 hours",
            dependencies=["task_final_review", "task_freight_booking"],
        ))
        
        return tasks
    
    def _distribute_tasks_across_days(
        self, 
        all_tasks: List[Task], 
        report: ExportReadinessReport
    ) -> List[DayPlan]:
        """
        Distribute tasks across 7 days based on dependencies and priorities.
        
        Strategy:
        - Day 1: Foundational tasks (GST LUT, HS code, IEC, bank)
        - Day 2-3: Certification applications (prioritized by urgency)
        - Day 4-5: Document preparation and certificates
        - Day 6: Logistics planning
        - Day 7: Final review and readiness check
        """
        # Build dependency graph
        task_map = {task.id: task for task in all_tasks}
        
        # Assign tasks to days based on their IDs and dependencies
        day_assignments: Dict[int, List[Task]] = {i: [] for i in range(1, 8)}
        
        # Day 1: Foundational tasks
        for task in all_tasks:
            if task.id in ["task_gst_lut", "task_hs_code_confirmation", "task_iec_verification", "task_bank_account_setup"]:
                day_assignments[1].append(task)
        
        # Day 2-3: Certification tasks
        cert_tasks = [t for t in all_tasks if t.category == TaskCategory.CERTIFICATION]
        # Split certifications across days 2 and 3
        mid_point = len(cert_tasks) // 2
        day_assignments[2].extend(cert_tasks[:mid_point] if mid_point > 0 else cert_tasks)
        if mid_point > 0:
            day_assignments[3].extend(cert_tasks[mid_point:])
        
        # Day 4-5: Document tasks
        doc_tasks = [
            t for t in all_tasks 
            if t.id in ["task_document_preparation", "task_certificate_of_origin", "task_packaging_compliance"]
        ]
        # Split document tasks
        if len(doc_tasks) > 0:
            day_assignments[4].append(doc_tasks[0])  # Document preparation on day 4
            day_assignments[5].extend(doc_tasks[1:])  # Rest on day 5
        
        # Day 6: Logistics tasks
        for task in all_tasks:
            if task.id in ["task_customs_broker", "task_freight_booking", "task_shipment_tracking"]:
                day_assignments[6].append(task)
        
        # Day 7: Final review tasks
        for task in all_tasks:
            if task.id in ["task_final_review", "task_readiness_checklist"]:
                day_assignments[7].append(task)
        
        # Create DayPlan objects
        day_titles = {
            1: "Foundation Setup - Documentation & Banking",
            2: "Certification Applications (Part 1)",
            3: "Certification Applications (Part 2)",
            4: "Document Preparation",
            5: "Certificates and Compliance",
            6: "Logistics Planning",
            7: "Final Review and Readiness Check",
        }
        
        day_plans = []
        for day_num in range(1, 8):
            tasks = day_assignments[day_num]
            # Ensure each day has at least one placeholder task
            if not tasks:
                tasks = [Task(
                    id=f"task_day{day_num}_placeholder",
                    title=f"Review Progress and Plan Ahead",
                    description=f"Review completed tasks and prepare for upcoming activities.",
                    category=TaskCategory.DOCUMENTATION,
                    estimated_duration="30 minutes",
                    dependencies=[],
                )]
            
            day_plans.append(DayPlan(
                day=day_num,
                title=day_titles[day_num],
                tasks=tasks
            ))
        
        return day_plans
    
    def prioritize_tasks(
        self, 
        certifications: List[Certification], 
        timeline: Dict
    ) -> List[Task]:
        """
        Prioritize tasks based on dependencies and timelines.
        
        Priority order:
        1. GST LUT (required before shipment)
        2. HS code confirmation (needed for certifications)
        3. Critical certifications (high priority, mandatory)
        4. Document preparation
        5. Logistics setup
        6. Final review
        
        Args:
            certifications: List of required certifications
            timeline: Timeline information from report
            
        Returns:
            List of tasks in priority order
        """
        # This method can be used for more sophisticated prioritization
        # Currently, the distribution logic handles prioritization
        pass
    
    def account_for_processing_times(self, tasks: List[Task]) -> ActionPlan:
        """
        Account for government processing times in the action plan.
        
        This method flags certifications requiring >7 days and creates interim steps.
        
        Args:
            tasks: List of tasks to process
            
        Returns:
            ActionPlan with processing time considerations
        """
        # This is handled in _generate_certification_tasks
        # where we check cert.estimated_timeline_days > 7
        pass
