# Copyright Thales 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Entrypoint for the knowledge_flow_app microservice.
"""

import argparse
import logging
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP
from rich.logging import RichHandler

from knowledge_flow_app.application_context import ApplicationContext
from knowledge_flow_app.common.structures import Configuration
from knowledge_flow_app.common.utils import parse_server_configuration
from knowledge_flow_app.controllers.content_controller import ContentController
from knowledge_flow_app.controllers.ingestion_controller import \
    IngestionController
from knowledge_flow_app.controllers.metadata_controller import \
    MetadataController
from knowledge_flow_app.controllers.vector_search_controller import \
    VectorSearchController
from knowledge_flow_app.controllers.knowledge_context_controller import \
    KnowledgeContextController


logger = logging.getLogger(__name__)
app: FastAPI = None  # Global app instance for optional reuse

def configure_logging():
    """Configure logging dynamically based on LOG_LEVEL environment variable."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        log_level = "INFO"
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[RichHandler(rich_tracebacks=False, show_time=False, show_path=False)],
    )
    logging.getLogger().info(f"Logging configured at {log_level} level.")
    
# --- After all the imports
logger = logging.getLogger(__name__)

def create_app(config_path: str = "./config/configuration.yaml", base_url: str = "/knowledge/v1") -> FastAPI:
    logger.info(f"🛠️ create_app() called with base_url={base_url}")
    configuration: Configuration = parse_server_configuration(config_path)
    ApplicationContext(configuration)

    app = FastAPI(
        docs_url=f"{base_url}/docs",
        redoc_url=f"{base_url}/redoc",
        openapi_url=f"{base_url}/openapi.json",
    )
    logger.info("✅ FastAPI instance created.")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=configuration.security.authorized_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    router = APIRouter()
    IngestionController(router)
    VectorSearchController(router)
    MetadataController(router)
    ContentController(router)
    KnowledgeContextController(router)

    logger.info("🧩 All controllers registered.")
    app.include_router(router, prefix=base_url)

    return app


def parse_cli_opts():
    configure_logging()
    dotenv_path = os.getenv("ENV_FILE", "./config/.env")
    dotenv_loaded = load_dotenv(dotenv_path)
    if dotenv_loaded:
        logging.getLogger().info(f"✅ Loaded environment variables from: {dotenv_path}")
    else:
        logging.getLogger().warning(f"⚠️  No .env file found at: {dotenv_path}")

    """
    Parses CLI arguments and starts the Uvicorn server.
    """
    parser = argparse.ArgumentParser(description="Start the knowledge_flow_app microservice")

    parser.add_argument("--config-path", dest="server_configuration_path", default="./config/configuration.yaml", help="Path to configuration YAML file")
    parser.add_argument("--base-url", dest="server_base_url_path", default="/knowledge/v1", help="Base path for all API endpoints")
    parser.add_argument("--server-address", dest="server_address", default="0.0.0.0", help="Server binding address")
    parser.add_argument("--server-port", dest="server_port", type=int, default=8111, help="Server port")
    parser.add_argument("--log-level", dest="server_log_level", default="info", help="Logging level")
    parser.add_argument("--server.reload", dest="server_reload", action="store_true", help="Enable auto-reload (for dev only)")
    parser.add_argument("--server.reloadDir", dest="server_reload_dir", type=str, help="watch for changes in these directories when auto-reload is enabled (for dev only)", default=".")

    return parser.parse_args()

args = parse_cli_opts()
app = create_app(args.server_configuration_path, args.server_base_url_path)
# MCP server to Knowledge Flow FastAPI app
mcp = FastApiMCP(
    app,  
    name="Knowledge Flow MCP",  # Name for the MCP server
    description="MCP server for Knowledge Flow",  # Description
    include_tags=["Vector Search"],
    describe_all_responses=True,  # Include all possible response schemas
    describe_full_response_schema=True  # Include full JSON schema in descriptions
)

# Mount the MCP server to Knowledge Flow FastAPI app
mcp.mount()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=args.server_address,
        port=args.server_port,
        log_level=args.server_log_level,
        reload=args.server_reload,
        reload_dirs=args.server_reload_dir
    )
