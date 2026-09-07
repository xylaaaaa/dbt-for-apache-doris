#!/usr/bin/env python
# encoding: utf-8

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from dataclasses import dataclass, field
from datetime import timezone

from dbt.adapters.base.relation import BaseRelation, EventTimeFilter, Policy


@dataclass
class DorisQuotePolicy(Policy):
    database: bool = True
    schema: bool = True
    identifier: bool = True


@dataclass
class DorisIncludePolicy(Policy):
    database: bool = True
    schema: bool = True
    identifier: bool = True


@dataclass(frozen=True, eq=False, repr=False)
class DorisRelation(BaseRelation):
    quote_policy: DorisQuotePolicy = field(default_factory=lambda: DorisQuotePolicy())
    include_policy: DorisIncludePolicy = field(default_factory=lambda: DorisIncludePolicy())
    quote_character: str = "`"

    def __post_init__(self):
        if self.database in ("", "None"):
            self.path.database = None

    def quoted(self, identifier):
        return "{}{}{}".format(
            self.quote_character,
            str(identifier).replace(self.quote_character, self.quote_character * 2),
            self.quote_character,
        )

    @staticmethod
    def _format_event_time_boundary(boundary):
        """Render dbt's UTC boundary for Doris's timezone-naive DATETIME."""
        if boundary.tzinfo is not None:
            boundary = boundary.astimezone(timezone.utc).replace(tzinfo=None)
        return boundary.strftime("%Y-%m-%d %H:%M:%S.%f").rstrip("0").rstrip(".")

    def _render_event_time_filtered(
        self,
        event_time_filter: EventTimeFilter,
    ) -> str:
        filters = []
        if event_time_filter.start:
            start = self._format_event_time_boundary(event_time_filter.start)
            filters.append(f"{event_time_filter.field_name} >= '{start}'")
        if event_time_filter.end:
            end = self._format_event_time_boundary(event_time_filter.end)
            filters.append(f"{event_time_filter.field_name} < '{end}'")
        return " and ".join(filters)
