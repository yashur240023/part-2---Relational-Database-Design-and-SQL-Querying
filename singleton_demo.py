import threading
import time

class DatabaseConnection:
    """
    Thread-Safe Singleton Implementation using Double-Checked Locking.
    Ensures exactly one shared database connection object exists.
    """
    _instance: Optional['DatabaseConnection'] = None
    _lock = threading.Lock()  # System-wide synchronization primitive

    def __new__(cls, *args, **kwargs):
        # First Check (Volatile/Unsynchronized check for optimal execution performance)
        if cls._instance is None:
            # Acquire lock because instance doesn't exist yet
            with cls._lock:
                # Second Check (Synchronized check to protect against race conditions)
                if cls._instance is None:
                    # Proceed to allocate memory and initialize the single instance
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
                    cls._instance._initialize_connection()
        return cls._instance

    def _initialize_connection(self) -> None:
        """Simulates heavy connection initialization workload."""
        self.connection_string = "postgresql://db_user:secure_pass@sars-db-cluster:5432/sars"
        self.is_connected = True
        # NAIVE LAZY INITIALIZATION COMMENTARY:
        # If multiple threads enter this instantiation block concurrently without the 
        # threading.Lock synchronization wrapper, Thread A could check `_instance is None`, 
        # find it True, and begin initialization. Before Thread A finishes assigning the 
        # variable, Context Switching shifts to Thread B. Thread B also checks `_instance is None`, 
        # finds it still True, and instantiates a separate second object block. This violates 
        # the Singleton principle and risks application state pollution and memory leaks.

    def get_connection(self) -> str:
        """Exposes the shared connection handle resource."""
        return self.connection_string


# --- Concurrent Verification Driver Code ---
def worker_task(thread_id: int, results: list) -> None:
    db_conn = DatabaseConnection()
    results.append(id(db_conn))

if __name__ == "__main__":
    threads = []
    execution_results = []
    
    # Fire 10 concurrent threads onto the Singleton creation path
    for i in range(10):
        t = threading.Thread(target=worker_task, args=(i, execution_results))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("--- Singleton Concurrency Evaluation ---")
    print(f"Generated Application Memory Addresses: {execution_results}")
    all_identical = all(address == execution_results[0] for address in execution_results)
    print(f"Verification Status: Unique Instance Confirmed? -> {all_identical}")
