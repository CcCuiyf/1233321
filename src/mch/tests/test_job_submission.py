import pytest
from unittest.mock import MagicMock, patch

def submit_job_logic(client, cluster_type, node_name):
    job_ids = { "S": 1001, "M": 2002, "L": 3003 }
    target_job_id = job_ids.get(cluster_type)
    if not target_job_id:
        raise ValueError("Invalid cluster type")
        
    run = client.jobs.run_now(
        job_id=target_job_id,
        notebook_params={"only_node": node_name}
    )
    return run.run_id

class TestJobSubmission:

    @patch('databricks.sdk.WorkspaceClient')
    def test_submit_job_dispatch_logic(self, MockWorkspaceClient):
        # 1. Prepare Mock
        mock_client = MockWorkspaceClient.return_value
        mock_run = MagicMock()
        mock_run.run_id = 999
        mock_client.jobs.run_now.return_value = mock_run

        # 2. Execute
        result = submit_job_logic(mock_client, "M", "Leukaemia")

        # 3. Assert
        assert result == 999
        
        # 4. Key verification: confirm it called the correct Job ID (2002) for M cluster
        mock_client.jobs.run_now.assert_called_once_with(
            job_id=2002,
            notebook_params={"only_node": "Leukaemia"}
        )