"""
Example usage of ComplianceTextAnalyzer service

This script demonstrates how to use the ComplianceTextAnalyzer service
for various compliance text analysis tasks.
"""
import logging
from compliance_text_analyzer import (
    ComplianceTextAnalyzer,
    extract_entities_from_text,
    extract_key_phrases_from_text,
    extract_compliance_terms_from_text,
    validate_compliance_document
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_entity_extraction():
    """Example: Extract entities from compliance text"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Entity Extraction")
    print("="*80)
    
    analyzer = ComplianceTextAnalyzer()
    
    text = """
    FDA approval is required for exporting pharmaceutical products to the United States.
    The application must be submitted to the Food and Drug Administration by January 15, 2024.
    Contact: Dr. John Smith, Regulatory Affairs Manager at Acme Pharmaceuticals.
    """
    
    print(f"\nInput Text:\n{text}")
    print("\nExtracted Entities:")
    print("-" * 80)
    
    try:
        entities = analyzer.extract_entities(text)
        
        for entity in entities:
            print(f"  {entity.text:30} | {entity.type:15} | Confidence: {entity.score:.2%}")
        
        print(f"\nTotal entities extracted: {len(entities)}")
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")


def example_entity_extraction_with_filter():
    """Example: Extract specific entity types"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Entity Extraction with Type Filtering")
    print("="*80)
    
    analyzer = ComplianceTextAnalyzer()
    
    text = """
    Export shipment from Mumbai, India to New York, USA scheduled for March 2024.
    Shipper: Global Exports Ltd. Consignee: American Imports Inc.
    """
    
    print(f"\nInput Text:\n{text}")
    print("\nExtracted Organizations and Locations:")
    print("-" * 80)
    
    try:
        entities = analyzer.extract_entities(
            text,
            filter_types=['ORGANIZATION', 'LOCATION']
        )
        
        for entity in entities:
            print(f"  {entity.text:30} | {entity.type:15} | Confidence: {entity.score:.2%}")
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")


def example_key_phrase_extraction():
    """Example: Extract key phrases from regulatory text"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Key Phrase Extraction")
    print("="*80)
    
    analyzer = ComplianceTextAnalyzer()
    
    text = """
    The product must comply with FDA regulations and obtain CE marking certification.
    REACH compliance is mandatory for chemical substances. ISO 9001 quality standards
    must be maintained throughout the manufacturing process. All documentation must
    include proper labeling requirements and safety data sheets.
    """
    
    print(f"\nInput Text:\n{text}")
    print("\nExtracted Key Phrases:")
    print("-" * 80)
    
    try:
        key_phrases = analyzer.extract_key_phrases(text)
        
        for phrase in key_phrases:
            print(f"  {phrase.text:50} | Confidence: {phrase.score:.2%}")
        
        print(f"\nTotal key phrases extracted: {len(key_phrases)}")
        
    except Exception as e:
        logger.error(f"Key phrase extraction failed: {e}")


def example_compliance_terms_extraction():
    """Example: Extract and categorize compliance terms"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Compliance Terms Extraction")
    print("="*80)
    
    analyzer = ComplianceTextAnalyzer()
    
    text = """
    Export requirements for LED lights to European Union:
    - CE marking certification required
    - RoHS compliance for restricted substances (lead, mercury, cadmium)
    - REACH regulation compliance mandatory
    - ISO 9001 quality management standard
    - DGFT export license from India
    - Customs clearance documentation
    - BIS certification for Indian standards
    
    Destination: Germany, France, Netherlands
    Regulatory bodies: European Commission, DGFT India
    """
    
    print(f"\nInput Text:\n{text}")
    
    try:
        compliance_terms = analyzer.extract_compliance_terms(text)
        
        print("\nExtracted Compliance Terms:")
        print("-" * 80)
        
        if compliance_terms.certifications:
            print(f"\n  Certifications ({len(compliance_terms.certifications)}):")
            for cert in compliance_terms.certifications:
                print(f"    - {cert}")
        
        if compliance_terms.regulations:
            print(f"\n  Regulations ({len(compliance_terms.regulations)}):")
            for reg in compliance_terms.regulations:
                print(f"    - {reg}")
        
        if compliance_terms.standards:
            print(f"\n  Standards ({len(compliance_terms.standards)}):")
            for std in compliance_terms.standards:
                print(f"    - {std}")
        
        if compliance_terms.restricted_substances:
            print(f"\n  Restricted Substances ({len(compliance_terms.restricted_substances)}):")
            for substance in compliance_terms.restricted_substances:
                print(f"    - {substance}")
        
        if compliance_terms.countries:
            print(f"\n  Countries ({len(compliance_terms.countries)}):")
            for country in compliance_terms.countries:
                print(f"    - {country}")
        
        if compliance_terms.organizations:
            print(f"\n  Organizations ({len(compliance_terms.organizations)}):")
            for org in compliance_terms.organizations:
                print(f"    - {org}")
        
    except Exception as e:
        logger.error(f"Compliance terms extraction failed: {e}")


def example_document_validation_invoice():
    """Example: Validate a commercial invoice"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Document Validation - Commercial Invoice")
    print("="*80)
    
    analyzer = ComplianceTextAnalyzer()
    
    invoice_text = """
    COMMERCIAL INVOICE
    
    Invoice No: INV-2024-001
    Date: January 15, 2024
    
    Exporter:
    Acme Manufacturing Ltd.
    123 Industrial Area, Mumbai, India
    GSTIN: 27AABCU9603R1ZM
    
    Importer:
    Global Imports LLC
    456 Business Park, New York, USA
    Tax ID: 12-3456789
    
    Product Description: LED Light Bulbs (HS Code: 8539.50)
    Quantity: 1000 units
    Unit Price: $10.00
    Total Value: $10,000.00
    
    Payment Terms: 30 days net
    Shipping Terms: FOB Mumbai
    """
    
    print(f"\nInvoice Text:\n{invoice_text}")
    
    try:
        validation = analyzer.validate_document(
            invoice_text,
            document_type='invoice'
        )
        
        print("\nValidation Results:")
        print("-" * 80)
        print(f"  Valid: {validation.is_valid}")
        print(f"  Compliance Score: {validation.compliance_score:.1f}/100")
        
        if validation.detected_issues:
            print(f"\n  Detected Issues ({len(validation.detected_issues)}):")
            for issue in validation.detected_issues:
                print(f"    - {issue}")
        else:
            print("\n  No issues detected ✓")
        
        if validation.suggestions:
            print(f"\n  Suggestions ({len(validation.suggestions)}):")
            for suggestion in validation.suggestions:
                print(f"    - {suggestion}")
        
        print(f"\n  Entities Found: {len(validation.entities)}")
        print(f"  Key Phrases Found: {len(validation.key_phrases)}")
        
    except Exception as e:
        logger.error(f"Document validation failed: {e}")


def example_document_validation_with_required_terms():
    """Example: Validate document with required terms"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Document Validation with Required Terms")
    print("="*80)
    
    analyzer = ComplianceTextAnalyzer()
    
    certificate_text = """
    CERTIFICATE OF ANALYSIS
    
    Product: Organic Turmeric Powder
    Batch No: TUR-2024-001
    
    This is to certify that the above product has been tested and meets
    the quality standards. The product is free from pesticides and
    heavy metals.
    
    Test Date: January 10, 2024
    Lab: Quality Testing Services Pvt. Ltd.
    """
    
    required_terms = ['FDA', 'organic', 'certificate', 'tested']
    
    print(f"\nCertificate Text:\n{certificate_text}")
    print(f"\nRequired Terms: {required_terms}")
    
    try:
        validation = analyzer.validate_document(
            certificate_text,
            required_terms=required_terms,
            document_type='certificate'
        )
        
        print("\nValidation Results:")
        print("-" * 80)
        print(f"  Valid: {validation.is_valid}")
        print(f"  Compliance Score: {validation.compliance_score:.1f}/100")
        
        if validation.missing_terms:
            print(f"\n  Missing Required Terms ({len(validation.missing_terms)}):")
            for term in validation.missing_terms:
                print(f"    - {term}")
        else:
            print("\n  All required terms present ✓")
        
        if validation.detected_issues:
            print(f"\n  Detected Issues ({len(validation.detected_issues)}):")
            for issue in validation.detected_issues:
                print(f"    - {issue}")
        
    except Exception as e:
        logger.error(f"Document validation failed: {e}")


def example_sentiment_analysis():
    """Example: Analyze sentiment in rejection reasons"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Sentiment Analysis")
    print("="*80)
    
    analyzer = ComplianceTextAnalyzer()
    
    texts = [
        "Product approved with excellent quality standards and proper documentation.",
        "Shipment rejected due to contamination and inadequate safety measures.",
        "Application pending review. Additional documentation required.",
        "Outstanding compliance record. Highly recommended for certification."
    ]
    
    for i, text in enumerate(texts, 1):
        print(f"\nText {i}: {text}")
        
        try:
            sentiment = analyzer.detect_sentiment(text)
            
            print(f"  Sentiment: {sentiment['sentiment']}")
            print(f"  Scores:")
            print(f"    Positive: {sentiment['scores']['positive']:.2%}")
            print(f"    Negative: {sentiment['scores']['negative']:.2%}")
            print(f"    Neutral:  {sentiment['scores']['neutral']:.2%}")
            print(f"    Mixed:    {sentiment['scores']['mixed']:.2%}")
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")


def example_convenience_functions():
    """Example: Using convenience functions"""
    print("\n" + "="*80)
    print("EXAMPLE 8: Convenience Functions")
    print("="*80)
    
    text = "FDA and CE marking required for export to United States"
    
    print(f"\nInput Text: {text}")
    print("\nUsing Convenience Functions:")
    print("-" * 80)
    
    try:
        # Quick entity extraction
        print("\n1. Quick Entity Extraction:")
        entities = extract_entities_from_text(text)
        for entity in entities:
            print(f"   {entity.text} ({entity.type})")
        
        # Quick key phrase extraction
        print("\n2. Quick Key Phrase Extraction:")
        key_phrases = extract_key_phrases_from_text(text)
        for phrase in key_phrases:
            print(f"   {phrase.text}")
        
        # Quick compliance terms extraction
        print("\n3. Quick Compliance Terms Extraction:")
        compliance_terms = extract_compliance_terms_from_text(text)
        print(f"   Certifications: {compliance_terms.certifications}")
        print(f"   Countries: {compliance_terms.countries}")
        
        # Quick document validation
        print("\n4. Quick Document Validation:")
        validation = validate_compliance_document(
            text,
            required_terms=['FDA', 'CE']
        )
        print(f"   Valid: {validation.is_valid}")
        print(f"   Score: {validation.compliance_score:.1f}/100")
        
    except Exception as e:
        logger.error(f"Convenience function failed: {e}")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("COMPLIANCE TEXT ANALYZER - EXAMPLE USAGE")
    print("="*80)
    print("\nNote: These examples use mock data. In production, AWS Comprehend")
    print("must be enabled and configured with valid credentials.")
    print("="*80)
    
    try:
        example_entity_extraction()
        example_entity_extraction_with_filter()
        example_key_phrase_extraction()
        example_compliance_terms_extraction()
        example_document_validation_invoice()
        example_document_validation_with_required_terms()
        example_sentiment_analysis()
        example_convenience_functions()
        
        print("\n" + "="*80)
        print("ALL EXAMPLES COMPLETED")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Example execution failed: {e}")


if __name__ == '__main__':
    main()
