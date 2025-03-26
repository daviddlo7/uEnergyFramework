from client.EnergyCollectorClient import EnergyCollectorClient

if __name__ == '__main__':
    # Example usage of the EnergyCollectorClient
    client = EnergyCollectorClient(host='localhost', port=50051)
    result = client.collect_energy(source="Solar Panel")
    print(f"Server Response: {result}")