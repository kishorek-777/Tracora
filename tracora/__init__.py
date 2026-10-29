import warnings

__version__ = "0.0.1"

# Suppress upstream Frappe v16 core framework deprecation warning emitted by frappe.share.get_shared and data_import
warnings.filterwarnings(
	"ignore",
	message=r"The 'limit_page_length' parameter is deprecated\. Use 'limit' instead\.",
)

