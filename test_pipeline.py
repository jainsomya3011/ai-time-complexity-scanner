from a2a_orchestrator import run_a2a_pipeline

code = """
for i in range(3):
    for j in range(3):
        print(i,j)
"""

result = run_a2a_pipeline(code)
print(result)