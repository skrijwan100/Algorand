from pyteal import *

# This smart contract is for a decentralized civic issue reporting platform.
# It allows users to create issues and vote on them using global state storage.

def approval_program():
    # --- Global State Keys ---
    issue_counter_key = Bytes("issue_counter")
    
    # For each issue, we'll store:
    # issue_<id>_title, issue_<id>_desc, issue_<id>_image, 
    # issue_<id>_owner, issue_<id>_votes
    # For voting, we'll use: voted_<user>_<issue_id> = 1

    # --- Contract Methods ---

    # on_creation: Initializes the application global state.
    on_creation = Seq([
        App.globalPut(issue_counter_key, Int(0)),
        Approve()
    ])

    # --- create_issue method ---
    on_create_issue = Seq([
        Assert(Txn.application_args.length() == Int(4)),

        # Get current issue ID
        (issue_id := ScratchVar(TealType.uint64)).store(App.globalGet(issue_counter_key)),

        # Store issue data in global state using simple keys
        App.globalPut(
            Concat(Bytes("issue_"), Itob(issue_id.load()), Bytes("_title")), 
            Txn.application_args[1]
        ),
        App.globalPut(
            Concat(Bytes("issue_"), Itob(issue_id.load()), Bytes("_desc")), 
            Txn.application_args[2]
        ),
        App.globalPut(
            Concat(Bytes("issue_"), Itob(issue_id.load()), Bytes("_image")), 
            Txn.application_args[3]
        ),
        App.globalPut(
            Concat(Bytes("issue_"), Itob(issue_id.load()), Bytes("_owner")), 
            Txn.sender()
        ),
        App.globalPut(
            Concat(Bytes("issue_"), Itob(issue_id.load()), Bytes("_votes")), 
            Int(0)
        ),
        App.globalPut(
            Concat(Bytes("issue_"), Itob(issue_id.load()), Bytes("_exists")), 
            Int(1)
        ),

        # Increment issue counter
        App.globalPut(issue_counter_key, issue_id.load() + Int(1)),

        Approve()
    ])

    # --- vote_for_issue method ---
    on_vote_for_issue = Seq([
        Assert(Txn.application_args.length() == Int(2)),

        (issue_id := ScratchVar(TealType.uint64)).store(Btoi(Txn.application_args[1])),

        # Check if issue exists
        Assert(
            App.globalGet(Concat(Bytes("issue_"), Itob(issue_id.load()), Bytes("_exists"))) == Int(1)
        ),

        # Check if user hasn't voted already using simple key
        (vote_key := Concat(Bytes("voted_"), Txn.sender(), Bytes("_"), Itob(issue_id.load()))),
        Assert(App.globalGet(vote_key) == Int(0)),

        # Get current vote count
        (votes_key := Concat(Bytes("issue_"), Itob(issue_id.load()), Bytes("_votes"))),
        (current_votes := App.globalGet(votes_key)),

        # Update vote count
        App.globalPut(votes_key, current_votes + Int(1)),

        # Mark that this user has voted on this issue
        App.globalPut(vote_key, Int(1)),

        Approve()
    ])

    # --- get_issue method ---
    on_get_issue = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        
        (query_issue_id := ScratchVar(TealType.uint64)).store(Btoi(Txn.application_args[1])),
        
        # Check if issue exists
        Assert(
            App.globalGet(Concat(Bytes("issue_"), Itob(query_issue_id.load()), Bytes("_exists"))) == Int(1)
        ),
        
        # Store query results in temporary global state for reading
        App.globalPut(
            Bytes("query_title"), 
            App.globalGet(Concat(Bytes("issue_"), Itob(query_issue_id.load()), Bytes("_title")))
        ),
        App.globalPut(
            Bytes("query_desc"), 
            App.globalGet(Concat(Bytes("issue_"), Itob(query_issue_id.load()), Bytes("_desc")))
        ),
        App.globalPut(
            Bytes("query_image"), 
            App.globalGet(Concat(Bytes("issue_"), Itob(query_issue_id.load()), Bytes("_image")))
        ),
        App.globalPut(
            Bytes("query_owner"), 
            App.globalGet(Concat(Bytes("issue_"), Itob(query_issue_id.load()), Bytes("_owner")))
        ),
        App.globalPut(
            Bytes("query_votes"), 
            App.globalGet(Concat(Bytes("issue_"), Itob(query_issue_id.load()), Bytes("_votes")))
        ),
        
        Approve()
    ])

    # --- get_issue_count method ---
    on_get_issue_count = Seq([
        App.globalPut(Bytes("total_issues"), App.globalGet(issue_counter_key)),
        Approve()
    ])

    # --- check_vote method ---
    on_check_vote = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        
        (check_issue_id := ScratchVar(TealType.uint64)).store(Btoi(Txn.application_args[1])),
        (check_user := ScratchVar(TealType.bytes)).store(Txn.application_args[2]),
        
        # Check if issue exists
        Assert(
            App.globalGet(Concat(Bytes("issue_"), Itob(check_issue_id.load()), Bytes("_exists"))) == Int(1)
        ),
        
        # Check if user has voted
        (user_vote_key := Concat(Bytes("voted_"), check_user.load(), Bytes("_"), Itob(check_issue_id.load()))),
        App.globalPut(Bytes("user_voted"), App.globalGet(user_vote_key)),
        
        Approve()
    ])

    # --- Main Program Logic ---
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Txn.sender() == Global.creator_address())],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Txn.sender() == Global.creator_address())],
        [Txn.on_completion() == OnComplete.OptIn, Approve()],
        [Txn.on_completion() == OnComplete.CloseOut, Approve()],
        [Txn.application_args[0] == Bytes("create_issue"), on_create_issue],
        [Txn.application_args[0] == Bytes("vote_for_issue"), on_vote_for_issue],
        [Txn.application_args[0] == Bytes("get_issue"), on_get_issue],
        [Txn.application_args[0] == Bytes("get_issue_count"), on_get_issue_count],
        [Txn.application_args[0] == Bytes("check_vote"), on_check_vote]
    )

    return program

def clear_state_program():
    return Approve()

if __name__ == "__main__":
    import os
    import json

    # Compile the approval program
    approval_teal = compileTeal(approval_program(), Mode.Application, version=8)
    
    # Compile the clear state program
    clear_teal = compileTeal(clear_state_program(), Mode.Application, version=8)

    path = os.path.dirname(os.path.abspath(__file__))

    # Write approval program to file
    with open(os.path.join(path, "approval.teal"), "w") as f:
        f.write(approval_teal)

    # Write clear state program to file
    with open(os.path.join(path, "clear.teal"), "w") as f:
        f.write(clear_teal)

    # Generate ABI contract file
    with open(os.path.join(path, "contract.json"), "w") as f:
        contract = {
            "name": "AlgoCivic",
            "methods": [
                {
                    "name": "create_issue",
                    "args": [
                        {"type": "string", "name": "title"},
                        {"type": "string", "name": "description"},
                        {"type": "string", "name": "image_url"}
                    ],
                    "returns": {"type": "void"}
                },
                {
                    "name": "vote_for_issue",
                    "args": [
                        {"type": "uint64", "name": "issue_id"}
                    ],
                    "returns": {"type": "void"}
                },
                {
                    "name": "get_issue",
                    "args": [
                        {"type": "uint64", "name": "issue_id"}
                    ],
                    "returns": {"type": "void"}
                },
                {
                    "name": "get_issue_count",
                    "args": [],
                    "returns": {"type": "void"}
                },
                {
                    "name": "check_vote",
                    "args": [
                        {"type": "uint64", "name": "issue_id"},
                        {"type": "address", "name": "user_address"}
                    ],
                    "returns": {"type": "void"}
                }
            ],
            "networks": {}
        }
        json.dump(contract, f, indent=4)
        
    print("TEAL and contract.json files generated successfully.")
    print(" - approval.teal")
    print(" - clear.teal") 
    print(" - contract.json")
    print("\nContract Methods:")
    print(" - create_issue(title, description, image_url)")
    print(" - vote_for_issue(issue_id)")
    print(" - get_issue(issue_id)")
    print(" - get_issue_count()")
    print(" - check_vote(issue_id, user_address)")
    print("\nData Storage:")
    print(" - Uses global state instead of boxes")
    print(" - Each issue gets multiple keys: issue_<id>_title, issue_<id>_desc, etc.")
    print(" - Voters stored as concatenated addresses in issue_<id>_voters")