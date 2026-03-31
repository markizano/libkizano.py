'''
JIRA ticket client.

Interfaces with JIRA for us in order to view ticket details and interact with JIRA.
I have used this too many times and get tired of copy-pasting code around.

Now with this, you can:

    import kizano
    work = kizano.tickets.Ticket('ABC-123')
    print(work.summary)
    print(work['description'])

and interface with it's attributes or dict-like items as if it were the ticket object itself.
'''
import os
import json
from jira import JIRA
from jira.resources import IssueType
from typing import Self, Any, Dict, Optional

JIRA_CLIENT = None
# Cache for field mappings to avoid repeated API calls
FIELD_MAPPING_CACHE: Optional[Dict[str, str]] = None
# Cache for issue types to avoid repeated API calls.
ISSUETYPE_MAPPING_CACHE: Optional[Dict[str, IssueType]] = None

COMMON_FIELDS = {
    'summary': 'summary',
    'description': 'description',
    'status': 'status',
    'assignee': 'assignee',
    'reporter': 'reporter',
    'priority': 'priority',
    'issue_type': 'issuetype',
    'created': 'created',
    'updated': 'updated',
    'resolution': 'resolution',
    'labels': 'labels',
    'components': 'components',
    'fix_versions': 'fixVersions',
    'affected_versions': 'versions',
    'environment': 'environment',
    'duedate': 'duedate',
    'time_estimate': 'timeestimate',
    'time_spent': 'timespent',
    'worklog': 'worklog',
    'comments': 'comment',
    'attachments': 'attachment',
    'subtasks': 'subtasks',
    'parent': 'parent',
    'epic_link': 'customfield_10014',  # Common Epic Link field
    'story_points': 'customfield_10016',  # Common Story Points field
}

class TicketNotFoundError(Exception):
    '''Exception raised when a JIRA ticket is not found or inaccessible.'''
    pass


class FieldNotFoundError(Exception):
    '''Exception raised when a field is not found in a JIRA ticket.'''
    pass

def getAtlassianSecrets():
    '''
    Gets the atlassian secrets from the environment.
    '''
    return {
        'atlassian_url': os.getenv('ATLASSIAN_URL'),
        'atlassian_user': os.getenv('ATLASSIAN_USER'),
        'atlassian_token': os.getenv('ATLASSIAN_TOKEN'),
    }

# Module-level Singleton like method
def getJiraClient() -> JIRA:
    '''
    If the JIRA client has not been initialized, connect and authenticate.

    Returns:
        The authenticated and connected JIRA client.
    '''
    global JIRA_CLIENT
    if JIRA_CLIENT is None:
        cfg = getAtlassianSecrets()
        JIRA_CLIENT = JIRA(
            server=cfg['atlassian_url'],
            basic_auth=(cfg['atlassian_user'], cfg['atlassian_token']),
        )
    return JIRA_CLIENT


def getFieldMappings() -> Dict[str, str]:
    '''
    Fetch all fields from JIRA and create a mapping of readable names to field IDs.

    Returns:
        Dictionary mapping field names (lowercase) to field IDs.
    '''
    global FIELD_MAPPING_CACHE
    if FIELD_MAPPING_CACHE is not None:
        return FIELD_MAPPING_CACHE

    client = getJiraClient()

    # Fetch all fields from JIRA
    fields = client.fields()

    # Create a mapping from readable names to field IDs
    FIELD_MAPPING_CACHE = {}
    for field in fields:
        field_id = field['id']
        field_name = field['name'].lower().replace(' ', '_')

        # Map readable name to field ID
        FIELD_MAPPING_CACHE[field_name] = field_id

        # Also map the original field ID itself
        FIELD_MAPPING_CACHE[field_id] = field_id

    return FIELD_MAPPING_CACHE

def getIssueTypes() -> Dict[str, IssueType]:
    '''
    Get the list of issue types available.

    Returns:
        Dictionary mapping of issue type by name to Issue object from JIRA API.
    '''
    global ISSUETYPE_MAPPING_CACHE
    if ISSUETYPE_MAPPING_CACHE is not None:
        return ISSUETYPE_MAPPING_CACHE

    client = getJiraClient()

    # Fetch all issue types from JIRA.
    issuetypes = client.issue_types()

    ISSUETYPE_MAPPING_CACHE = {}
    for issuetype in issuetypes:
        name = issuetype.name
        ISSUETYPE_MAPPING_CACHE[name] = issuetype

    return ISSUETYPE_MAPPING_CACHE

class Ticket:
    '''
    Comprehensive JIRA ticket abstraction layer.
    Provides access to both built-in and custom JIRA fields through __getitem__() and __getattr__() methods.

    Features:
    - Lazy loading of ticket data
    - Support for both built-in and custom fields
    - Caching to avoid repeated API calls
    - Error handling for missing tickets or fields
    - Type hints for better IDE support
    - Both bracket and dot notation access

    Example:
        t = Ticket('ABC-123')
        # Bracket notation
        print(t['summary'])  # Built-in field
        print(t['customfield_12345'])  # Custom field

        # Dot notation
        print(t.summary)  # Built-in field
        print(t.description)  # Built-in field
        print(t.assignee)  # Built-in field with nested data
    '''

    @classmethod
    def create(cls, project: str, summary: str, description: str, issuetype: str, **kwargs) -> Self:
        '''
        Factory Method:
        Creates a new issue based on the input fields and returns a new Ticket() object as a result.
        This method makes it easy to create a new issue without having to worry about authentication
        outside of this context.

        This allows exceptions to pass thru so you can handle them outside of this context.
        '''
        client = getJiraClient()
        issuetypes = getIssueTypes()
        assert project != '', 'Project cannot be empty!'
        assert summary != '', 'Summary must have some text!'
        assert issuetype != '', 'Issue Type is required!'
        assert issuetype in issuetypes.keys(), f'IssueType must be one of: {", ".join(issuetypes.keys())}'
        issue_details = {
            'project': project,
            'summary': summary,
            'description': description,
            'issuetype': issuetype,
            **kwargs,
        }
        issue = client.create_issue(fields=issue_details)
        return cls(issue.key)

    def __init__(self, ticket_id: str, jira_client: Optional[JIRA] = None):
        '''
        Initialize a JIRA ticket client.

        Args:
            ticket_id: The JIRA ticket ID (e.g., 'ABC-123')
            jira_client: Optional pre-configured JIRA client. If not provided,
                        will create one using configuration.
        '''
        self.ticket_id = ticket_id.upper()
        self._jira_client = jira_client or getJiraClient()
        self._ticket_data: Dict[str, Any] = {}
        self._loaded = False

    def _load_ticket_data(self) -> None:
        '''Load ticket data from JIRA if not already loaded.'''
        if not self._loaded:
            try:
                # Fetch ticket with all fields using the jira package
                issue = self._jira_client.issue(self.ticket_id, expand='changelog')
                # Convert the issue object to a dictionary-like structure
                self._ticket_data = {
                    'fields': issue.raw['fields'],
                    'key': issue.key,
                    'id': issue.id
                }
                self._loaded = True
            except Exception as e:
                raise TicketNotFoundError(f"Ticket {self.ticket_id} not found or inaccessible: {str(e)}")

    def __getitem__(self, field_name: str) -> Any:
        '''
        Get a field value from the JIRA ticket using bracket notation.

        Args:
            field_name: The field name (built-in or custom field ID)

        Returns:
            The field value, which could be a string, dict, list, or other type

        Raises:
            FieldNotFoundError: If the field doesn't exist
            TicketNotFoundError: If the ticket doesn't exist or is inaccessible
        '''
        return self._get_field_value(field_name)

    def __getattr__(self, field_name: str) -> Any:
        '''
        Get a field value from the JIRA ticket using dot notation.

        Args:
            field_name: The field name (built-in or custom field ID)

        Returns:
            The field value, which could be a string, dict, list, or other type

        Raises:
            FieldNotFoundError: If the field doesn't exist
            TicketNotFoundError: If the ticket doesn't exist or is inaccessible
        '''
        # Skip private attributes and methods to avoid conflicts
        if field_name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{field_name}'")

        return self._get_field_value(field_name)

    def _get_field_value(self, field_name: str) -> Any:
        '''
        Internal method to get a field value from the JIRA ticket.

        Args:
            field_name: The field name (built-in or custom field ID)

        Returns:
            The field value, which could be a string, dict, list, or other type

        Raises:
            FieldNotFoundError: If the field doesn't exist
            TicketNotFoundError: If the ticket doesn't exist or is inaccessible
        '''
        self._load_ticket_data()

        if not self._ticket_data:
            raise TicketNotFoundError(f"Ticket {self.ticket_id} not found")

        # Handle nested field access (e.g., 'assignee.displayName')
        if '.' in field_name:
            return self._get_nested_field(field_name)

        # First check if we're trying to get a top-level item.
        if field_name == 'id':
            return self._ticket_data['id']

        if field_name == 'key':
            return self._ticket_data['key']

        # Get field mapping from JIRA
        field_mapping = getFieldMappings()

        # Check if field exists in the ticket data
        if field_name not in self._ticket_data.get('fields', {}):
            # Try common field mappings
            mapped_field = self._map_common_fields(field_name)
            if mapped_field and mapped_field in self._ticket_data.get('fields', {}):
                field_name = mapped_field
            else:
                # Try to find the field using JIRA field mapping
                # First try the field name as-is
                search_name = field_name.lower()
                if search_name in field_mapping:
                    jira_field_id = field_mapping[search_name]
                    if jira_field_id in self._ticket_data.get('fields', {}):
                        field_name = jira_field_id
                    else:
                        raise FieldNotFoundError(f"Field '{field_name}' (mapped to '{jira_field_id}') not found in ticket {self.ticket_id}")
                else:
                    raise FieldNotFoundError(f"Field '{field_name}' not found in ticket {self.ticket_id}")

        return self._ticket_data['fields'][field_name]

    def _get_nested_field(self, field_path: str) -> Any:
        '''Get a nested field value using dot notation.'''
        parts = field_path.split('.')
        current = self._ticket_data['fields']

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise FieldNotFoundError(f"Nested field '{field_path}' not found in ticket {self.ticket_id}")

        return current

    def _map_common_fields(self, field_name: str) -> Optional[str]:
        '''Map common field names to their JIRA field IDs.'''
        return COMMON_FIELDS.get(field_name.lower())

    def get_field_names(self) -> list:
        '''
        Get all available field names for this ticket.

        Returns:
            List of field names (both built-in and custom)
        '''
        self._load_ticket_data()
        if not self._ticket_data:
            return []
        return list(self._ticket_data.get('fields', {}).keys())

    def get_custom_fields(self) -> Dict[str, Any]:
        '''
        Get all custom fields for this ticket.

        Returns:
            Dictionary of custom field ID to value mappings
        '''
        self._load_ticket_data()
        if not self._ticket_data:
            return {}

        custom_fields = {}
        for field_id, value in self._ticket_data.get('fields', {}).items():
            if field_id.startswith('customfield_'):
                custom_fields[field_id] = value

        return custom_fields

    def as_dict(self) -> Dict[str, Any]:
        '''
        Return this ticket as a JSON-ready dictionary including all known fields.
        '''
        self._load_ticket_data()
        ticket_fields = self._ticket_data.get('fields', {})

        fields: Dict[str, Dict[str, Any]] = {
            'id': self._ticket_data.get('id'),
            'key': self._ticket_data.get('key'),
        }
        for field_name in COMMON_FIELDS.keys():
            fields[field_name] = ticket_fields.get(field_name)

        return fields

    def json(self, indent: int = 2, sort_keys: bool = True) -> str:
        '''
        Return this ticket, including all known fields, as JSON.
        '''
        return json.dumps(self.as_dict(), indent=indent, sort_keys=sort_keys, default=str)

    def refresh(self) -> None:
        '''Refresh ticket data from JIRA.'''
        self._loaded = False
        self._ticket_data = {}
        self._load_ticket_data()

    def __str__(self) -> str:
        '''String representation of the ticket.'''
        try:
            self._load_ticket_data()
            if self._ticket_data:
                summary = self._ticket_data.get('fields', {}).get('summary', 'No summary')
                status = self._ticket_data.get('fields', {}).get('status', {}).get('name', 'Unknown')
                return f"{self.ticket_id}: {summary} [{status}]"
            return f"{self.ticket_id}: Not loaded"
        except Exception:
            return f"{self.ticket_id}: Error loading"

    def __repr__(self) -> str:
        '''Representation of the ticket object.'''
        return f"Ticket('{self.ticket_id}')"
