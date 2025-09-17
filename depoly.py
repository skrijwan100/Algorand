
import logging
import json
import os
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from algokit_utils import (
    ApplicationClient,
    ApplicationSpecification,
    OnComplete,
    Account,
    get_account,
    get_algod_client,
    get_indexer_client,
)

logger = logging.getLogger(__name__)

# define deployment behaviour based on supplied app spec
def deploy() -> None:
    # Set up Algorand client and deployer account
    algod_client = get_algod_client()
    indexer_client = get_indexer_client()
    deployer = get_account(algod_client, "DEPLOYER")

    # Get the path to the contract artifacts
    contract_path = os.path.join(os.path.dirname(__file__), "..", "contracts")

    # Load the application specification from the TEAL and ABI JSON files
    with open(os.path.join(contract_path, "approval.teal"), "r") as f:
        approval_program = f.read()
    with open(os.path.join(contract_path, "clear.teal"), "r") as f:
        clear_program = f.read()
    with open(os.path.join(contract_path, "contract.json"), "r") as f:
        abi = json.load(f)

    app_spec = ApplicationSpecification(
        approval_program=approval_program,
        clear_state_program=clear_program,
        contract=abi,
    )

    # Create an ApplicationClient
    app_client = ApplicationClient(
        algod_client,
        app_spec,
        creator=deployer,
    )

    # Deploy the app
    logger.info("Deploying the AlgoCivic application...")
    response = app_client.create()
    app_id = response.app_id
    app_address = response.app_address
    logger.info(f"Application deployed with App ID: {app_id} and App Address: {app_address}")
    
    # Update the contractInfo.json file with the new app ID
    contract_info_path = os.path.join(contract_path, "contractInfo.json")
    with open(contract_info_path, "r+") as f:
        data = json.load(f)
        data['appId'] = app_id
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        
    logger.info(f"Updated 'appId' in {contract_info_path} to {app_id}")
    logger.info("Deployment complete.")


if __name__ == "__main__":
    # You will need to set the environment variables for your deployer account's mnemonic
    # For example:
    # export DEPLOYER_MNEMONIC="your 25-word mnemonic phrase here"
    #
    # You may also need to configure your network connection if not using the default LocalNet
    # See https://github.com/algorand-algokit/algokit-utils-py for more details
    deploy()
