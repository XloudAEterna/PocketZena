from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_partial_search():
    # Test 1: "pika" should return "pikachu"
    print("Test 1: Ricerca di 'pika'...")
    response = client.get("/api/v1/zenamon/search?name=pika")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "pikachu"
    print(f"✓ Trovato: {data['name']}")

    # Test 2: "char" should return "charmander" (primo match alfabetico/lista)
    print("Test 2: Ricerca di 'char'...")
    response = client.get("/api/v1/zenamon/search?name=char")
    assert response.status_code == 200
    data = response.json()
    assert data["name"].startswith("char")
    print(f"✓ Trovato: {data['name']}")

    # Test 3: "mew" (esatto)
    print("Test 3: Ricerca di 'mew' (esatto)...")
    response = client.get("/api/v1/zenamon/search?name=mew")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "mew"
    print(f"✓ Trovato: {data['name']}")

    # Test 4: Nome inesistente
    print("Test 4: Ricerca di 'xyz123'...")
    response = client.get("/api/v1/zenamon/search?name=xyz123")
    assert response.status_code == 404
    print("✓ Correttamente non trovato")

if __name__ == "__main__":
    try:
        test_partial_search()
        print("\nTutti i test di ricerca parziale sono passati!")
    except Exception as e:
        print(f"\nTest fallito: {e}")
        exit(1)
