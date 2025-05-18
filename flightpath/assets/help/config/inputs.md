# Inputs

The inputs section determines where CsvPath Framework looks for staged data and prepared named-paths groups. Along with the <i>results</i> section's <i>archive</i> setting, this is the core operating environment for the Framework.

Inputs can live on any of the five storage backends CsvPath Framework supports:
- The file system, local or mounted
- An SFTP server
- AWS S3
- Azure Blob Storage
- Google Cloud Storage

Using any of the latter four backends requires two things:
- A URL using the protocol identifiers <i>sftp</i>, <i>s3</i>, <i>azure</i>, or <i>gcs</i>, respectively
- Configuration of access control tokens and secrets in environment variables

In the case of the cloud services, the access control setup is the same as a Python developer would do in order to use the Python library published by Amazon, Microsoft, or Google. In the case of SFTP, see the listeners configuration section for setup.

Briefly, the <i>files</i> area is not where your MFT should land arriving files. It is intended to be an area where files are immutable. MFT entry points are generally not immutable, and in some cases may even verge on chaotic. Files should be registered with the CsvPath Framework for it to take over management. When you are using FlightPath you can right-click on a data file and select <i>Stage data</i> to register it with the Framework. In an automated production environment commonly a simple two-line script is triggered by MFT when a file arrives. Using a Lambda or a workflow system like Airflow is also common.

The <i>csvpaths</i> area is where your named-paths groups live. Again, this is a hands-off area for CsvPath Framework to manage within an automated context. You can load csvpaths into named-paths groups by right-clicking on a csvpath file and selecting <i>Load csvpaths</i>.

