"""Farm Data Provider: the ONLY place that touches the Farm Database.

Other components never write SQL; they talk to FarmDataProvider
(see architecture document, section 7.2.1 and the Repository pattern in 7.6).
"""
