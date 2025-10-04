from enum import Enum

class ChartType(Enum):
    """Chart type enumeration with camelCase values"""
    LINE_CHART = "lineChart"
    BAR_CHART = "barChart"
    AREA_CHART = "areaChart"
    GAUGE = "gauge"
    HEATMAP = "heatmap"

class ChartLibrary(Enum):
    """Chart library enumeration"""
    RECHARTS = "recharts"
    PLOTLY = "plotly"

class ChartConfig:
    """Chart configuration mapping between chart types and libraries"""
    
    # Mapping of chart types to their corresponding libraries
    CHART_TYPE_TO_LIBRARY = {
        ChartType.LINE_CHART: ChartLibrary.RECHARTS,
        ChartType.BAR_CHART: ChartLibrary.RECHARTS,
        ChartType.AREA_CHART: ChartLibrary.RECHARTS,
        ChartType.GAUGE: ChartLibrary.PLOTLY,
        ChartType.HEATMAP: ChartLibrary.PLOTLY,
    }
    
    @classmethod
    def get_library_for_chart_type(cls, chart_type: ChartType) -> ChartLibrary:
        """Get the appropriate library for a given chart type"""
        return cls.CHART_TYPE_TO_LIBRARY.get(chart_type)
    
    @classmethod
    def get_chart_config(cls, chart_type: ChartType) -> dict:
        """Get complete chart configuration for a given chart type"""
        library = cls.get_library_for_chart_type(chart_type)
        return {
            "chartType": chart_type.value,
            "chartLibrary": library.value
        }
    
    @classmethod
    def get_all_chart_types(cls) -> list:
        """Get all available chart types as string values"""
        return [chart_type.value for chart_type in ChartType]
    
    @classmethod
    def get_recharts_types(cls) -> list:
        """Get chart types that use Recharts library"""
        return [
            chart_type.value for chart_type, library in cls.CHART_TYPE_TO_LIBRARY.items()
            if library == ChartLibrary.RECHARTS
        ]
    
    @classmethod
    def get_plotly_types(cls) -> list:
        """Get chart types that use Plotly library"""
        return [
            chart_type.value for chart_type, library in cls.CHART_TYPE_TO_LIBRARY.items()
            if library == ChartLibrary.PLOTLY
        ]
