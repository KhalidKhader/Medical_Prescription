"""
Brand Search Module
Handles brand name searching in RxNorm using brand-specific queries
"""

class SearchServiceDriver:
    """Service for brand-specific drug searching in RxNorm"""
    
    def __init__(self, driver):
        self.driver = driver
