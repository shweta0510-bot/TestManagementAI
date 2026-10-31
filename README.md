# TestManagementAI

Automation suites for the Zara platform.

The pending-pipeline feature does not create a pipeline on every run. `features/pending_pipeline.feature` asks the Zara pipeline repository (`data/zara_pipelines.json`) whether any pipeline is still **Pending Setup**.

- If one is pending, the `@end-to-end` scenario is skipped. Finish setup on that pipeline in Zara.
- If none are pending, creation runs once and the new pipeline is stored in the repository. The next run reuses it.

```bash
python -m zara_platform
python -m unittest discover -s tests
```
