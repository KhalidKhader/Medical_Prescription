"""
Pydantic models and schemas for prescription processing.
Defines the strict JSON structure for prescription data extraction.
"""

from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


class Prescriber(BaseModel):
    """Prescriber information model"""
    full_name: Optional[str] = Field(None, description="Full name of the prescriber")
    state_license_number: Optional[str] = Field(None, description="State medical license number")
    npi_number: Optional[str] = Field(None, description="National Provider Identifier")
    dea_number: Optional[str] = Field(None, description="DEA registration number")
    address: Optional[str] = Field(None, description="Prescriber's address")
    contact_number: Optional[str] = Field(None, description="Contact phone number")
    certainty: Optional[int] = Field(None, description="Confidence score (0-100)")


class Patient(BaseModel):
    """Patient information model"""
    full_name: Optional[str] = Field(None, description="Full name of the patient")
    date_of_birth: Optional[str] = Field(None, description="Patient's date of birth")
    age: Optional[str] = Field(None, description="Patient's age")
    facility_name: Optional[str] = Field(None, description="Facility or institution name")
    address: Optional[str] = Field(None, description="Patient's address")
    certainty: Optional[int] = Field(None, description="Confidence score (0-100)")


class Medication(BaseModel):
    """Medication information model"""
    drug_name: Optional[str] = Field(None, description="Name of the medication")
    strength: Optional[str] = Field(None, description="Medication strength/dosage")
    instructions_for_use: Optional[str] = Field(None, description="Original prescription instructions")
    quantity: Optional[Union[str, int]] = Field(None, description="Quantity prescribed")
    infer_qty: Optional[str] = Field(None, description="Whether quantity was inferred (Yes/No)")
    days_of_use: Optional[Union[str, int]] = Field(None, description="Days of use")
    infer_days: Optional[str] = Field(None, description="Whether days of use was inferred (Yes/No)")
    rxcui: Optional[str] = Field(None, description="RxNorm concept unique identifier")
    ndc: Optional[str] = Field(None, description="National Drug Code")
    drug_schedule: Optional[str] = Field(None, description="DEA controlled substance schedule")
    brand_drug: Optional[str] = Field(None, description="Brand name drug")
    brand_ndc: Optional[str] = Field(None, description="Brand drug NDC")
    sig_english: Optional[str] = Field(None, description="Clear English instructions")
    sig_spanish: Optional[str] = Field(None, description="Spanish translation of instructions")
    refills: Optional[Union[str, int]] = Field(None, description="Number of refills")
    certainty: Optional[int] = Field(None, description="Confidence score (0-100)")


class Prescription(BaseModel):
    """Complete prescription model"""
    prescriber: Prescriber = Field(..., description="Prescriber information")
    patient: Patient = Field(..., description="Patient information")
    date_prescription_written: Optional[str] = Field(None, description="Date prescription was written")
    medications: List[Medication] = Field(default_factory=list, description="List of prescribed medications")


class PrescriptionProcessingResponse(BaseModel):
    """Response model for prescription processing"""
    processing_id: str = Field(..., description="Unique processing identifier")
    status: str = Field(..., description="Processing status (completed/failed)")
    processing_time_seconds: float = Field(..., description="Total processing time in seconds")
    prescription_data: Optional[Dict[str, Any]] = Field(None, description="Extracted prescription data")
    supervisor_report: Optional[str] = Field(None, description="Quality assurance report")
    quality_warnings: List[str] = Field(default_factory=list, description="Quality warnings and issues")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
